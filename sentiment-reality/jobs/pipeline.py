"""
Pipeline orchestration module.

Provides run_pipeline_for_ticker() which runs the full pipeline:
1. Ingest news -> upsert items
2. Score unscored -> insert item_scores
3. Ingest prices -> upsert prices_daily + compute return_1d
4. Aggregate daily -> upsert daily_agg
5. Metrics windowed -> upsert metrics_windowed
"""
from datetime import datetime
from db import execute, fetch_all, get_connection


def run_pipeline_for_ticker(
    ticker: str,
    news_hours: int = 48,
    score_limit: int | None = None,
    prices_days: int = 180,
    agg_days: int = 90,
    metrics_days: int = 90,
    window_days: int = 7,
    window_days_list: list[int] | None = None,
) -> dict:
    """
    Run the full data pipeline for a single ticker.

    Args:
        ticker: Stock symbol (e.g., 'TSLA')
        news_hours: Hours of news to fetch (default 48)
        score_limit: Max items to score (None = unlimited/200)
        prices_days: Calendar days of prices to fetch (default 180)
        agg_days: Days of daily aggregates to compute (default 90)
        metrics_days: Days of metrics to compute (default 90)
        window_days: Rolling window size for metrics (default 7)
        window_days_list: List of window sizes to compute (e.g., [7, 14, 30])

    Returns:
        Summary dict with counts from each step
    """
    ticker = ticker.upper()
    started = datetime.now()

    # Determine which windows to compute
    windows = window_days_list or [window_days]

    print(f"\n{'='*60}")
    print(f"PIPELINE: {ticker}")
    print(f"  news_hours={news_hours}, score_limit={score_limit}")
    print(f"  prices_days={prices_days}, agg_days={agg_days}")
    print(f"  metrics_days={metrics_days}, windows={windows}")
    print(f"{'='*60}")

    summary = {
        "ticker": ticker,
        "started_at": started.isoformat(),
        "steps": {},
        "success": False,
    }

    try:
        # Step 1: Ingest news
        print("\n[1/5] Ingesting news...")
        news_result = ingest_items(ticker, hours=news_hours)
        summary["steps"]["ingest_news"] = news_result
        print(f"      → Inserted {news_result.get('inserted', 0)}, skipped {news_result.get('skipped', 0)}")

        # Step 2: Score unscored items
        print("\n[2/5] Scoring items...")
        limit = score_limit if score_limit else 200
        score_result = score_items(ticker, limit=limit)
        summary["steps"]["score_items"] = score_result
        print(f"      → Scored {score_result.get('scored', 0)}/{score_result.get('selected', 0)}")

        # Step 3: Ingest prices
        print("\n[3/5] Ingesting prices...")
        prices_result = ingest_prices(ticker, days=prices_days)
        summary["steps"]["ingest_prices"] = prices_result
        print(f"      → Stored {prices_result.get('count', 0)} price records")

        # Step 4: Compute daily aggregates
        print("\n[4/5] Computing daily aggregates...")
        agg_result = compute_daily_agg(ticker, days=agg_days)
        summary["steps"]["daily_agg"] = agg_result
        print(f"      → Updated {agg_result.get('count', 0)} daily aggregates")

        # Step 5: Compute metrics for all window sizes
        print("\n[5/5] Computing metrics...")
        metrics_results = {}
        total_metrics = 0
        for wd in windows:
            result = compute_metrics_windowed(ticker, window_days=wd, days=metrics_days)
            metrics_results[f"window_{wd}"] = result
            total_metrics += result.get("count", 0)
            print(f"      → Window {wd}d: {result.get('count', 0)} rows")
        summary["steps"]["metrics"] = metrics_results
        print(f"      → Total: {total_metrics} metric rows")

        summary["success"] = True

    except Exception as e:
        summary["error"] = str(e)
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()

    elapsed = (datetime.now() - started).total_seconds()
    summary["elapsed_seconds"] = round(elapsed, 2)

    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE: {ticker} in {elapsed:.1f}s")
    print(f"{'='*60}\n")

    return summary


# ============================================================
# Step implementations
# ============================================================

def ingest_items(ticker: str, hours: int) -> dict:
    """Ingest news items from NewsAPI."""
    from ingest_to_db import ingest_news_to_db
    result = ingest_news_to_db(ticker, hours=hours)
    return {
        "total": result.get("total_articles", 0),
        "inserted": result.get("inserted_count", 0),
        "skipped": result.get("skipped_count", 0),
        "errors": len(result.get("errors", [])),
    }


def score_items(ticker: str, limit: int) -> dict:
    """Score unscored items using ML model."""
    from score_unscored_items import score_unscored_items
    result = score_unscored_items(ticker, limit=limit)
    return {
        "selected": result.get("selected", 0),
        "scored": result.get("scored", 0),
        "skipped_no_text": result.get("skipped_no_text", 0),
        "errors": result.get("errors", 0),
    }


def ingest_prices(ticker: str, days: int) -> dict:
    """Ingest prices and compute returns."""
    from providers.prices import fetch_daily_prices

    prices = fetch_daily_prices(ticker, days=days)
    if not prices:
        return {"count": 0}

    # Upsert prices
    count = 0
    for p in prices:
        execute("""
            INSERT INTO prices_daily (ticker, date, open, high, low, close, adj_close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                adj_close = EXCLUDED.adj_close,
                volume = EXCLUDED.volume
        """, (ticker, p["date"], p["open"], p["high"], p["low"], p["close"], p["adj_close"], p["volume"]))
        count += 1

    # Compute return_1d using LAG for previous trading day
    execute("""
        WITH returns AS (
            SELECT
                ticker,
                date,
                (close - LAG(close) OVER (PARTITION BY ticker ORDER BY date)) /
                    NULLIF(LAG(close) OVER (PARTITION BY ticker ORDER BY date), 0) * 100 AS return_1d
            FROM prices_daily
            WHERE ticker = %s
        )
        UPDATE prices_daily p
        SET return_1d = r.return_1d
        FROM returns r
        WHERE p.ticker = r.ticker AND p.date = r.date
    """, (ticker,))

    return {"count": count}


def compute_daily_agg(ticker: str, days: int) -> dict:
    """Compute daily aggregates from scored items."""
    from datetime import date, timedelta

    cutoff_date = date.today() - timedelta(days=days)

    # Get aggregates grouped by day
    rows = fetch_all("""
        SELECT
            DATE(i.published_at) as date,
            AVG(s.sentiment_score) as sentiment_avg,
            COUNT(*) as article_count,
            SUM(CASE WHEN s.sentiment_label = 'POSITIVE' THEN 1 ELSE 0 END) as positive_count,
            SUM(CASE WHEN s.sentiment_label = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral_count,
            SUM(CASE WHEN s.sentiment_label = 'NEGATIVE' THEN 1 ELSE 0 END) as negative_count
        FROM items i
        JOIN item_scores s ON i.id = s.item_id
        WHERE i.ticker = %s AND DATE(i.published_at) >= %s
        GROUP BY DATE(i.published_at)
        ORDER BY date
    """, (ticker, cutoff_date))

    if not rows:
        return {"count": 0}

    # Upsert each day
    count = 0
    for row in rows:
        execute("""
            INSERT INTO daily_agg (ticker, date, sentiment_avg, article_count,
                                   positive_count, neutral_count, negative_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date) DO UPDATE SET
                sentiment_avg = EXCLUDED.sentiment_avg,
                article_count = EXCLUDED.article_count,
                positive_count = EXCLUDED.positive_count,
                neutral_count = EXCLUDED.neutral_count,
                negative_count = EXCLUDED.negative_count
        """, (
            ticker,
            row["date"],
            float(row["sentiment_avg"]) if row["sentiment_avg"] else 0,
            row["article_count"],
            row["positive_count"],
            row["neutral_count"],
            row["negative_count"],
        ))
        count += 1

    return {"count": count}


def compute_metrics_windowed(ticker: str, window_days: int, days: int) -> dict:
    """Compute rolling window metrics."""
    import numpy as np
    from datetime import date, timedelta

    cutoff_date = date.today() - timedelta(days=days)

    # Get daily_agg data
    sentiments = fetch_all("""
        SELECT date, sentiment_avg
        FROM daily_agg
        WHERE ticker = %s AND date >= %s
        ORDER BY date
    """, (ticker, cutoff_date))

    # Get prices with returns
    prices = fetch_all("""
        SELECT date, return_1d
        FROM prices_daily
        WHERE ticker = %s AND return_1d IS NOT NULL AND date >= %s
        ORDER BY date
    """, (ticker, cutoff_date))

    if not sentiments or not prices:
        return {"count": 0}

    # Build lookup dicts
    sentiment_by_date = {str(s["date"]): s["sentiment_avg"] for s in sentiments}
    return_by_date = {str(p["date"]): p["return_1d"] for p in prices}

    # Get all dates we have both sentiment and returns
    common_dates = sorted(set(sentiment_by_date.keys()) & set(return_by_date.keys()))

    if len(common_dates) < window_days:
        return {"count": 0}

    count = 0
    for i in range(window_days - 1, len(common_dates)):
        window_dates = common_dates[i - window_days + 1 : i + 1]
        date_end = window_dates[-1]

        sentiments_window = [sentiment_by_date[d] for d in window_dates]
        returns_window = [return_by_date[d] for d in window_dates]

        # Compute metrics
        metrics = _compute_window_metrics(sentiments_window, returns_window)

        # Upsert
        execute("""
            INSERT INTO metrics_windowed
                (ticker, date_end, window_days, corr, directional_match,
                 alignment_score, misalignment_days, interpretation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date_end, window_days) DO UPDATE SET
                corr = EXCLUDED.corr,
                directional_match = EXCLUDED.directional_match,
                alignment_score = EXCLUDED.alignment_score,
                misalignment_days = EXCLUDED.misalignment_days,
                interpretation = EXCLUDED.interpretation
        """, (
            ticker,
            date_end,
            window_days,
            metrics["corr"],
            metrics["directional_match"],
            metrics["alignment_score"],
            metrics["misalignment_days"],
            metrics["interpretation"],
        ))
        count += 1

    return {"count": count}


def _compute_window_metrics(sentiments: list, returns: list) -> dict:
    """Compute metrics for a single window."""
    import numpy as np

    sentiments = np.array(sentiments, dtype=float)
    returns = np.array(returns, dtype=float)

    # Correlation
    if np.std(sentiments) < 0.001 or np.std(returns) < 0.001:
        corr = 0.0
    else:
        corr = float(np.corrcoef(sentiments, returns)[0, 1])
        if np.isnan(corr):
            corr = 0.0

    # Directional match
    sent_signs = np.sign(sentiments)
    ret_signs = np.sign(returns)
    matches = np.sum(sent_signs == ret_signs)
    directional_match = float(matches / len(sentiments))

    # Misalignment days
    misalignment_days = int(len(sentiments) - matches)

    # Alignment score
    alignment_score = 0.5 * corr + 0.5 * (directional_match * 2 - 1)
    alignment_score = max(-1.0, min(1.0, alignment_score))

    # Interpretation
    if alignment_score >= 0.3:
        interpretation = "Aligned"
    elif alignment_score <= -0.3:
        interpretation = "Misleading"
    else:
        interpretation = "Noisy"

    return {
        "corr": float(round(corr, 4)),
        "directional_match": float(round(directional_match, 4)),
        "alignment_score": float(round(alignment_score, 4)),
        "misalignment_days": int(misalignment_days),
        "interpretation": interpretation,
    }
