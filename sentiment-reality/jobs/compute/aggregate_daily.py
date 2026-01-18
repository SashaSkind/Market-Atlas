"""Compute daily sentiment aggregates from item_scores."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import query, execute

def compute_daily_aggregates(ticker: str):
    """
    Compute daily_agg rows from item_scores joined to items.

    - Groups by day
    - Calculates sentiment_avg, article_count, label counts
    - Upserts into daily_agg table
    """
    print(f"Computing daily aggregates for {ticker}")

    # Get all scored items for this ticker, grouped by day
    rows = query("""
        SELECT
            DATE(i.published_at) as date,
            AVG(s.sentiment_score) as sentiment_avg,
            COUNT(*) as article_count,
            SUM(CASE WHEN s.sentiment_label = 'POSITIVE' THEN 1 ELSE 0 END) as positive_count,
            SUM(CASE WHEN s.sentiment_label = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral_count,
            SUM(CASE WHEN s.sentiment_label = 'NEGATIVE' THEN 1 ELSE 0 END) as negative_count
        FROM items i
        JOIN item_scores s ON i.id = s.item_id
        WHERE i.ticker = %s
        GROUP BY DATE(i.published_at)
        ORDER BY date
    """, (ticker,))

    if not rows:
        print(f"No scored items found for {ticker}")
        return 0

    # Upsert each day's aggregate
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
            row["sentiment_avg"],
            row["article_count"],
            row["positive_count"],
            row["neutral_count"],
            row["negative_count"],
        ))
        count += 1

    print(f"Upserted {count} daily aggregates for {ticker}")
    return count


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        compute_daily_aggregates(sys.argv[1])
    else:
        print("Usage: python aggregate_daily.py <TICKER>")
