"""
Task worker - polls tasks table and executes jobs.

Task types:
- BACKFILL_STOCK: Full backfill for a ticker (90 days)
- REFRESH_STOCK: Refresh recent data for a ticker (2-3 days)
- DAILY_UPDATE_ALL: Enqueue REFRESH_STOCK for all active tickers
"""
import time
from datetime import datetime
from db import query, execute, get_connection
from providers.prices import fetch_daily_prices
from providers.news import fetch_headlines
from ml.sentiment import score_text
from compute.aggregate_daily import compute_daily_aggregates
from compute.metrics import compute_metrics


def claim_next_task():
    """
    Claim the next pending task using FOR UPDATE SKIP LOCKED.
    Returns task dict or None if no tasks available.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, task_type, ticker, payload, attempts
                FROM tasks
                WHERE status = 'PENDING'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """)
            row = cur.fetchone()
            if not row:
                return None

            task_id, task_type, ticker, payload, attempts = row

            # Mark as RUNNING
            cur.execute("""
                UPDATE tasks
                SET status = 'RUNNING', attempts = attempts + 1, updated_at = now()
                WHERE id = %s
            """, (task_id,))
            conn.commit()

            return {
                "id": task_id,
                "task_type": task_type,
                "ticker": ticker,
                "payload": payload,
                "attempts": attempts + 1,
            }


def complete_task(task_id: str, error: str = None):
    """Mark task as DONE or ERROR."""
    if error:
        execute("""
            UPDATE tasks
            SET status = 'ERROR', error = %s, updated_at = now()
            WHERE id = %s
        """, (error[:500], task_id))
    else:
        execute("""
            UPDATE tasks
            SET status = 'DONE', updated_at = now()
            WHERE id = %s
        """, (task_id,))


def handle_backfill_stock(ticker: str):
    """Full backfill for a ticker: prices, news, scores, aggregates, metrics."""
    print(f"=== BACKFILL_STOCK: {ticker} ===")

    # 1. Fetch and store prices
    print("Fetching prices...")
    prices = fetch_daily_prices(ticker, days=90)
    store_prices(ticker, prices)
    compute_returns(ticker)

    # 2. Fetch and store news
    print("Fetching news...")
    headlines = fetch_headlines(ticker, days=90)
    store_items(ticker, headlines)

    # 3. Score unscored items
    print("Scoring items...")
    score_unscored_items(ticker)

    # 4. Compute aggregates
    print("Computing aggregates...")
    compute_daily_aggregates(ticker)

    # 5. Compute metrics
    print("Computing metrics...")
    compute_metrics(ticker, window_days=7)

    print(f"=== BACKFILL_STOCK: {ticker} COMPLETE ===")


def handle_refresh_stock(ticker: str):
    """Refresh recent data for a ticker (last 3 days)."""
    print(f"=== REFRESH_STOCK: {ticker} ===")

    # Same as backfill but for fewer days
    prices = fetch_daily_prices(ticker, days=5)
    store_prices(ticker, prices[-3:] if len(prices) >= 3 else prices)
    compute_returns(ticker)

    headlines = fetch_headlines(ticker, days=3)
    store_items(ticker, headlines)

    score_unscored_items(ticker)
    compute_daily_aggregates(ticker)
    compute_metrics(ticker, window_days=7)

    print(f"=== REFRESH_STOCK: {ticker} COMPLETE ===")


def handle_daily_update_all():
    """Enqueue REFRESH_STOCK for all active tickers."""
    print("=== DAILY_UPDATE_ALL ===")
    tickers = query("SELECT ticker FROM tracked_stocks WHERE is_active = true")
    for row in tickers:
        execute("""
            INSERT INTO tasks (task_type, ticker, priority, status)
            VALUES ('REFRESH_STOCK', %s, 20, 'PENDING')
        """, (row["ticker"],))
        print(f"Enqueued REFRESH_STOCK for {row['ticker']}")
    print("=== DAILY_UPDATE_ALL COMPLETE ===")


def store_prices(ticker: str, prices: list):
    """Upsert prices into prices_daily."""
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
    print(f"Stored {len(prices)} prices for {ticker}")


def compute_returns(ticker: str):
    """Compute return_1d for prices."""
    execute("""
        UPDATE prices_daily p
        SET return_1d = (p.close - prev.close) / prev.close * 100
        FROM prices_daily prev
        WHERE p.ticker = %s
          AND prev.ticker = p.ticker
          AND prev.date = p.date - INTERVAL '1 day'
    """, (ticker,))


def store_items(ticker: str, items: list):
    """Insert items (dedupe by source+url)."""
    count = 0
    for item in items:
        try:
            execute("""
                INSERT INTO items (ticker, source, source_id, published_at, title, url, snippet)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source, url) DO NOTHING
            """, (
                ticker,
                item["source"],
                item.get("source_id"),
                item["published_at"],
                item["title"],
                item["url"],
                item.get("snippet"),
            ))
            count += 1
        except Exception as e:
            print(f"Error inserting item: {e}")
    print(f"Stored {count} items for {ticker}")


def score_unscored_items(ticker: str):
    """Score items that don't have scores yet."""
    # Get unscored items
    unscored = query("""
        SELECT i.id, i.title
        FROM items i
        LEFT JOIN item_scores s ON i.id = s.item_id AND s.model = 'hf_fin_v1'
        WHERE i.ticker = %s AND s.item_id IS NULL
    """, (ticker,))

    if not unscored:
        print(f"No unscored items for {ticker}")
        return

    print(f"Scoring {len(unscored)} items for {ticker}")
    for item in unscored:
        result = score_text(item["title"])
        execute("""
            INSERT INTO item_scores (item_id, model, sentiment_label, sentiment_score, confidence)
            VALUES (%s, 'hf_fin_v1', %s, %s, %s)
            ON CONFLICT (item_id, model) DO NOTHING
        """, (item["id"], result["label"], result["sentiment_score"], result["confidence"]))

    print(f"Scored {len(unscored)} items for {ticker}")


def run_once():
    """Process one task and return."""
    task = claim_next_task()
    if not task:
        return False

    print(f"\nProcessing task: {task['task_type']} - {task['ticker']}")

    try:
        if task["task_type"] == "BACKFILL_STOCK":
            handle_backfill_stock(task["ticker"])
        elif task["task_type"] == "REFRESH_STOCK":
            handle_refresh_stock(task["ticker"])
        elif task["task_type"] == "DAILY_UPDATE_ALL":
            handle_daily_update_all()
        else:
            raise ValueError(f"Unknown task type: {task['task_type']}")

        complete_task(task["id"])
        print(f"Task {task['id']} completed successfully")

    except Exception as e:
        print(f"Task {task['id']} failed: {e}")
        complete_task(task["id"], error=str(e))

    return True


def run_loop(poll_interval: int = 10):
    """Continuously poll for tasks."""
    print("Starting worker loop...")
    while True:
        try:
            if not run_once():
                print(f"No tasks, sleeping {poll_interval}s...")
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(poll_interval)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_once()
    else:
        run_loop()
