"""Compute rolling window metrics (sentiment vs price alignment)."""
import sys
sys.path.insert(0, '..')
from db import query, execute
import numpy as np
from datetime import date, timedelta

def compute_metrics(ticker: str, window_days: int = 7):
    """
    Compute rolling metrics for ticker.

    For each date_end, computes over the previous window_days:
    - corr: correlation between sentiment_avg and return_1d
    - directional_match: fraction of days where sign(sentiment) == sign(return)
    - alignment_score: composite score
    - misalignment_days: count of days where signs differ
    - interpretation: "Aligned" | "Noisy" | "Misleading"

    Upserts into metrics_windowed table.
    """
    print(f"Computing {window_days}-day metrics for {ticker}")

    # Get daily_agg data
    sentiments = query("""
        SELECT date, sentiment_avg
        FROM daily_agg
        WHERE ticker = %s
        ORDER BY date
    """, (ticker,))

    # Get prices with returns
    prices = query("""
        SELECT date, return_1d
        FROM prices_daily
        WHERE ticker = %s AND return_1d IS NOT NULL
        ORDER BY date
    """, (ticker,))

    if not sentiments or not prices:
        print(f"Not enough data for {ticker}")
        return 0

    # Build lookup dicts
    sentiment_by_date = {str(s["date"]): s["sentiment_avg"] for s in sentiments}
    return_by_date = {str(p["date"]): p["return_1d"] for p in prices}

    # Get all dates we have both sentiment and returns
    common_dates = sorted(set(sentiment_by_date.keys()) & set(return_by_date.keys()))

    if len(common_dates) < window_days:
        print(f"Not enough common dates for {ticker} (need {window_days}, have {len(common_dates)})")
        return 0

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

    print(f"Computed {count} window metrics for {ticker}")
    return count


def _compute_window_metrics(sentiments: list, returns: list) -> dict:
    """
    Compute metrics for a single window.

    Formula for alignment_score:
    - 0.5 * correlation + 0.5 * directional_match
    - Clamped to [-1, 1]

    Interpretation thresholds:
    - alignment_score >= 0.3: "Aligned"
    - alignment_score <= -0.3: "Misleading"
    - else: "Noisy"
    """
    sentiments = np.array(sentiments)
    returns = np.array(returns)

    # Correlation (handle edge cases)
    if np.std(sentiments) < 0.001 or np.std(returns) < 0.001:
        corr = 0.0
    else:
        corr = float(np.corrcoef(sentiments, returns)[0, 1])
        if np.isnan(corr):
            corr = 0.0

    # Directional match
    # sign(0) = 0, so we count it as matching if both are ~0
    sent_signs = np.sign(sentiments)
    ret_signs = np.sign(returns)
    matches = np.sum(sent_signs == ret_signs)
    directional_match = matches / len(sentiments)

    # Misalignment days
    misalignment_days = int(len(sentiments) - matches)

    # Alignment score (composite)
    alignment_score = 0.5 * corr + 0.5 * (directional_match * 2 - 1)  # Scale dm to [-1,1]
    alignment_score = max(-1.0, min(1.0, alignment_score))

    # Interpretation
    if alignment_score >= 0.3:
        interpretation = "Aligned"
    elif alignment_score <= -0.3:
        interpretation = "Misleading"
    else:
        interpretation = "Noisy"

    return {
        "corr": round(corr, 4),
        "directional_match": round(directional_match, 4),
        "alignment_score": round(alignment_score, 4),
        "misalignment_days": misalignment_days,
        "interpretation": interpretation,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        compute_metrics(sys.argv[1])
    else:
        print("Usage: python metrics.py <TICKER>")
