"""Dashboard endpoint - reads from DB only."""
from fastapi import APIRouter, Query
from datetime import date, timedelta
from schemas import (
    DashboardData, DashboardDataWithHeadlines, DailyDataPoint, PricePoint, DailySentiment,
    WindowMetric, SentimentSummary, PriceSummary, AlignmentSummary, NewsItem, Coverage
)

router = APIRouter()

# Try to import db, fall back to mock data if DB not configured
try:
    from db import query, is_configured
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False
    def is_configured():
        return False


@router.get("/api/dashboard", response_model=DashboardDataWithHeadlines)
@router.get("/dashboard", response_model=DashboardDataWithHeadlines, include_in_schema=False)
def get_dashboard(
    ticker: str = Query("TSLA"),
    period: int = Query(30),
    headlines_limit: int = Query(3, ge=1, le=20),
):
    """
    Get dashboard data for a ticker.
    Reads from DB only: prices_daily, daily_agg, metrics_windowed, items + item_scores.
    Never calls external APIs or ML models.
    """
    ticker = ticker.upper()

    if not DB_AVAILABLE or not is_configured():
        return _mock_dashboard(ticker, period)

    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=period)

        # Fetch prices
        prices = query("""
            SELECT date, close, adj_close, volume
            FROM prices_daily
            WHERE ticker = %s AND date >= %s
            ORDER BY date ASC
        """, (ticker, start_date))

        # Fetch daily sentiment aggregates
        sentiments = query("""
            SELECT date, sentiment_avg, article_count,
                   positive_count, neutral_count, negative_count
            FROM daily_agg
            WHERE ticker = %s AND date >= %s
            ORDER BY date ASC
        """, (ticker, start_date))

        # Fetch windowed metrics (7-day)
        metrics = query("""
            SELECT date_end, corr, directional_match, alignment_score,
                   misalignment_days, interpretation
            FROM metrics_windowed
            WHERE ticker = %s AND window_days = 7 AND date_end >= %s
            ORDER BY date_end ASC
        """, (ticker, start_date))

        # Fetch recent headlines with scores
        headlines_raw = query("""
            SELECT
                i.id::text,
                i.title,
                i.source,
                i.published_at,
                s.sentiment_label,
                s.sentiment_score,
                s.confidence,
                i.snippet,
                i.url
            FROM items i
            LEFT JOIN item_scores s ON i.id = s.item_id AND s.model = 'hf_fin_v1'
            WHERE i.ticker = %s
            ORDER BY i.published_at DESC
            LIMIT %s
        """, (ticker, headlines_limit))

        # Build daily_data by joining on date
        prices_by_date = {str(p["date"]): p for p in prices}
        sentiments_by_date = {str(s["date"]): s for s in sentiments}
        metrics_by_date = {str(m["date_end"]): m for m in metrics}

        all_dates = sorted(set(prices_by_date.keys()) | set(sentiments_by_date.keys()))

        daily_data = []
        for d in all_dates:
            p = prices_by_date.get(d)
            s = sentiments_by_date.get(d)
            m = metrics_by_date.get(d)

            daily_data.append(DailyDataPoint(
                date=d,
                price=PricePoint(
                    date=d,
                    close=p["close"],
                    adj_close=p.get("adj_close"),
                    volume=p.get("volume")
                ) if p else None,
                sentiment=DailySentiment(
                    date=d,
                    avg_score=s["sentiment_avg"],
                    article_count=s["article_count"],
                    positive_count=s["positive_count"],
                    neutral_count=s["neutral_count"],
                    negative_count=s["negative_count"]
                ) if s else None,
                metric=WindowMetric(
                    date_end=d,
                    corr=m.get("corr"),
                    directional_match=m.get("directional_match"),
                    alignment_score=m.get("alignment_score"),
                    misalignment_days=m.get("misalignment_days"),
                    interpretation=m.get("interpretation")
                ) if m else None
            ))

        # Build headlines list
        headlines = []
        for h in headlines_raw:
            headlines.append(NewsItem(
                id=h.get("id"),
                title=h.get("title", "No title"),
                source=h.get("source"),
                published_at=str(h["published_at"]) if h.get("published_at") else None,
                sentiment_label=h.get("sentiment_label"),
                sentiment_score=float(h["sentiment_score"]) if h.get("sentiment_score") else None,
                confidence=float(h["confidence"]) if h.get("confidence") else None,
                snippet=h.get("snippet"),
                url=h.get("url"),
            ))

        # Compute summaries
        sentiment_summary = _compute_sentiment_summary(sentiments)
        price_summary = _compute_price_summary(prices)
        alignment_summary = _compute_alignment_summary(metrics)
        coverage = _compute_coverage(ticker, period)

        return DashboardDataWithHeadlines(
            ticker=ticker,
            period=period,
            sentiment_summary=sentiment_summary,
            price_summary=price_summary,
            alignment=alignment_summary,
            daily_data=daily_data,
            headlines=headlines,
            coverage=coverage,
        )

    except Exception as e:
        # Fall back to mock if DB query fails
        print(f"DB error: {e}")
        import traceback
        traceback.print_exc()
        return _mock_dashboard(ticker, period)


def _compute_sentiment_summary(sentiments: list) -> SentimentSummary:
    """Compute sentiment summary from daily aggregates."""
    if not sentiments:
        return SentimentSummary()

    # Use period average instead of just latest day
    current_score = sum(s["sentiment_avg"] for s in sentiments) / len(sentiments)

    # Compute trend (compare last 3 days if available)
    if len(sentiments) >= 3:
        recent_avg = sum(s["sentiment_avg"] for s in sentiments[-3:]) / 3
        older_avg = sum(s["sentiment_avg"] for s in sentiments[-6:-3]) / 3 if len(sentiments) >= 6 else current_score
        if recent_avg > older_avg + 0.05:
            trend = "up"
        elif recent_avg < older_avg - 0.05:
            trend = "down"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # Dominant label
    total_pos = sum(s["positive_count"] for s in sentiments)
    total_neu = sum(s["neutral_count"] for s in sentiments)
    total_neg = sum(s["negative_count"] for s in sentiments)
    if total_pos >= total_neu and total_pos >= total_neg:
        dominant = "POSITIVE"
    elif total_neg >= total_pos and total_neg >= total_neu:
        dominant = "NEGATIVE"
    else:
        dominant = "NEUTRAL"

    return SentimentSummary(
        current_score=round(current_score, 3),
        trend=trend,
        dominant_label=dominant
    )


def _compute_price_summary(prices: list) -> PriceSummary:
    """Compute price summary from daily prices."""
    if not prices:
        return PriceSummary()

    current_price = prices[-1]["close"]
    if len(prices) >= 2:
        first_price = prices[0]["close"]
        period_return = round((current_price - first_price) / first_price * 100, 2)
    else:
        period_return = 0.0

    return PriceSummary(
        current_price=round(current_price, 2),
        period_return=period_return
    )


def _compute_alignment_summary(metrics: list) -> AlignmentSummary:
    """Compute alignment summary from windowed metrics."""
    if not metrics:
        return AlignmentSummary()

    latest = metrics[-1]
    return AlignmentSummary(
        score=latest.get("alignment_score"),
        misalignment_days=latest.get("misalignment_days"),
        interpretation=latest.get("interpretation")
    )


def _compute_coverage(ticker: str, period: int) -> Coverage:
    """Compute sentiment coverage for requested period."""
    start_date = date.today() - timedelta(days=period)

    result = query("""
        SELECT COUNT(*) as count, MIN(date) as min_date, MAX(date) as max_date
        FROM daily_agg
        WHERE ticker = %s AND date >= %s
    """, (ticker, start_date))

    row = result[0] if result else {}
    days_available = row.get("count", 0) or 0

    return Coverage(
        sentiment_days_available=days_available,
        sentiment_period_requested=period,
        sentiment_period_used=min(period, days_available),
        coverage_start=str(row["min_date"]) if row.get("min_date") else None,
        coverage_end=str(row["max_date"]) if row.get("max_date") else None,
    )


def _mock_dashboard(ticker: str, period: int) -> DashboardDataWithHeadlines:
    """Return mock data when DB is not available."""
    from datetime import date, timedelta
    import random

    daily_data = []
    base_price = {"SPY": 450, "TSLA": 245, "AAPL": 185, "NVDA": 520, "JPM": 195, "PFE": 28, "GME": 22}.get(ticker, 100)

    for i in range(min(period, 14)):
        d = (date.today() - timedelta(days=period-i-1)).isoformat()
        price_change = random.uniform(-0.02, 0.02)
        base_price *= (1 + price_change)
        sentiment = random.uniform(-0.3, 0.5)

        daily_data.append(DailyDataPoint(
            date=d,
            price=PricePoint(date=d, close=round(base_price, 2), volume=random.randint(500000, 2000000)),
            sentiment=DailySentiment(
                date=d,
                avg_score=round(sentiment, 3),
                article_count=random.randint(5, 30),
                positive_count=random.randint(2, 15),
                neutral_count=random.randint(1, 10),
                negative_count=random.randint(0, 8)
            ),
            metric=WindowMetric(
                date_end=d,
                alignment_score=round(random.uniform(-0.5, 0.8), 2),
                misalignment_days=random.randint(0, 3),
                interpretation=random.choice(["Aligned", "Noisy", "Misleading"])
            )
        ))

    # Mock headlines
    headlines = [
        NewsItem(
            id="mock-1",
            title=f"{ticker} shares move on earnings sentiment",
            source="MockNews",
            published_at=date.today().isoformat(),
            sentiment_label="POSITIVE",
            confidence=0.85,
            snippet="Mock headline for demo purposes."
        ),
        NewsItem(
            id="mock-2",
            title=f"Analysts discuss {ticker} outlook",
            source="MockAnalysis",
            published_at=(date.today() - timedelta(days=1)).isoformat(),
            sentiment_label="NEUTRAL",
            confidence=0.72,
        ),
    ]

    return DashboardDataWithHeadlines(
        ticker=ticker,
        period=period,
        sentiment_summary=SentimentSummary(
            current_score=round(random.uniform(-0.2, 0.4), 2),
            trend=random.choice(["up", "down", "stable"]),
            dominant_label=random.choice(["POSITIVE", "NEUTRAL", "NEGATIVE"])
        ),
        price_summary=PriceSummary(
            current_price=round(base_price, 2),
            period_return=round(random.uniform(-5, 8), 2)
        ),
        alignment=AlignmentSummary(
            score=round(random.uniform(-0.3, 0.7), 2),
            misalignment_days=random.randint(1, 5),
            interpretation=random.choice(["Aligned", "Noisy", "Misleading"])
        ),
        daily_data=daily_data,
        headlines=headlines,
    )
