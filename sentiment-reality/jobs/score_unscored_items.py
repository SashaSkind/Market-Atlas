"""
Score unscored items: Query items without scores and run ML sentiment analysis.

This queries the DB for items that don't have a score for model='hf_fin_v1',
fetches the full article text, runs sentiment scoring, and writes results.
"""
from db import fetch_all, execute, is_configured
from ingest_news import get_article_text
from ml.sentiment import score_text


def score_unscored_items(ticker: str, limit: int = 25) -> dict:
    """
    Find and score items that don't have sentiment scores yet.

    Args:
        ticker: Stock symbol (e.g., 'TSLA')
        limit: Max items to process in one run (default 25)

    Returns:
        Summary dict with:
        - ticker: str
        - selected: int (items found without scores)
        - scored: int (successfully scored)
        - skipped_no_text: int (no text available)
        - errors: int (scoring/DB errors)
    """
    summary = {
        "ticker": ticker,
        "selected": 0,
        "scored": 0,
        "skipped_no_text": 0,
        "errors": 0,
    }

    if not is_configured():
        print("ERROR: Database not configured. Set DATABASE_URL in .env")
        return summary

    # Query for items without scores for model='hf_fin_v1'
    print(f"Finding unscored items for {ticker} (limit {limit})...")

    unscored = fetch_all("""
        SELECT i.id, i.url, i.title, i.snippet
        FROM items i
        LEFT JOIN item_scores s
            ON s.item_id = i.id AND s.model = 'hf_fin_v1'
        WHERE i.ticker = %s
            AND s.item_id IS NULL
        ORDER BY i.published_at DESC
        LIMIT %s
    """, (ticker, limit))

    summary["selected"] = len(unscored)

    if not unscored:
        print(f"No unscored items found for {ticker}")
        return summary

    print(f"Found {len(unscored)} unscored items")

    for i, item in enumerate(unscored):
        item_id = item["id"]
        url = item["url"]
        title = item["title"] or ""
        snippet = item["snippet"] or ""

        print(f"  [{i + 1}/{len(unscored)}] {title[:50]}...")

        try:
            # Try to get full article text
            text = get_article_text(url)

            # Fallback to title + snippet if extraction fails
            if not text or not text.strip():
                fallback_text = title
                if snippet:
                    fallback_text += "\n\n" + snippet
                text = fallback_text.strip()

            # Skip if still no text
            if not text:
                print(f"    -> Skipped: no text available")
                summary["skipped_no_text"] += 1
                continue

            # Score the text
            result = score_text(text)

            # Insert into item_scores (idempotent with ON CONFLICT DO NOTHING)
            execute("""
                INSERT INTO item_scores (item_id, model, sentiment_label, sentiment_score, confidence)
                VALUES (%s, 'hf_fin_v1', %s, %s, %s)
                ON CONFLICT (item_id, model) DO NOTHING
            """, (
                item_id,
                result["sentiment_label"],
                result["sentiment_score"],
                result["confidence"],
            ))

            print(f"    -> {result['sentiment_label']} ({result['sentiment_score']:.2f}, {result['chunks_used']} chunks)")
            summary["scored"] += 1

        except Exception as e:
            print(f"    -> Error: {e}")
            summary["errors"] += 1
            continue

    return summary


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python score_unscored_items.py <TICKER> [limit]")
        print("Example: python score_unscored_items.py TSLA 25")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 25

    print(f"\n=== Scoring unscored items for {ticker} ===\n")
    result = score_unscored_items(ticker, limit=limit)

    print(f"\n=== Summary ===")
    print(f"  Ticker: {result['ticker']}")
    print(f"  Selected: {result['selected']}")
    print(f"  Scored: {result['scored']}")
    print(f"  Skipped (no text): {result['skipped_no_text']}")
    print(f"  Errors: {result['errors']}")
    print()
