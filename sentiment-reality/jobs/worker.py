"""
Task worker - polls tasks table and executes jobs.

Task types:
- DAILY_UPDATE_ALL: Run full pipeline for all active tickers
- REFRESH_STOCK: Refresh data for a single ticker (user-triggered)
- BACKFILL_STOCK: Full 30-day backfill for a single ticker
- BACKFILL_DEFAULTS: Backfill all 5 default tickers (TSLA, NVDA, JPM, PFE, GME)

Safe claiming uses FOR UPDATE SKIP LOCKED to prevent double-processing.
"""
import time
import json
from db import fetch_all, execute, get_connection
from pipeline import run_pipeline_for_ticker

# Default parameters for each task type
DAILY_PARAMS = {
    "news_hours": 48,
    "score_limit": 200,
    "prices_days": 180,
    "agg_days": 90,
    "metrics_days": 90,
    "window_days": 7,
}

REFRESH_PARAMS = {
    "news_hours": 48,
    "score_limit": 50,
    "prices_days": 180,
    "agg_days": 30,
    "metrics_days": 30,
    "window_days": 7,
}

BACKFILL_PARAMS = {
    "news_hours": 720,      # 30 days of news
    "score_limit": 500,     # Higher limit for backfill
    "prices_days": 180,
    "agg_days": 30,
    "metrics_days": 30,
    "window_days_list": [7, 14, 30],  # Multiple windows
}

DEFAULT_TICKERS = ["TSLA", "NVDA", "JPM", "PFE", "GME"]

MAX_ATTEMPTS = 3


def claim_next_task() -> dict | None:
    """
    Claim the next pending task using FOR UPDATE SKIP LOCKED.
    Returns task dict or None if no tasks available.

    Uses atomic CTE to claim in a single query.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Atomic claim using CTE
            cur.execute("""
                WITH next AS (
                    SELECT id
                    FROM tasks
                    WHERE status = 'PENDING'
                    ORDER BY priority DESC, created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE tasks t
                SET status = 'RUNNING', attempts = attempts + 1, updated_at = now()
                FROM next
                WHERE t.id = next.id
                RETURNING t.id, t.task_type, t.ticker, t.payload, t.attempts
            """)
            row = cur.fetchone()
            conn.commit()

            if not row:
                return None

            task_id, task_type, ticker, payload, attempts = row

            return {
                "id": str(task_id),
                "task_type": task_type,
                "ticker": ticker,
                "payload": payload or {},
                "attempts": attempts,
            }


def complete_task(task_id: str, result: dict = None, error: str = None):
    """Mark task as DONE or ERROR with optional result/error info."""
    if error:
        execute("""
            UPDATE tasks
            SET status = 'ERROR',
                error = %s,
                updated_at = now()
            WHERE id = %s
        """, (error[:1000], task_id))
    else:
        # Store result in payload if provided
        if result:
            execute("""
                UPDATE tasks
                SET status = 'DONE',
                    payload = COALESCE(payload, '{}'::jsonb) || %s,
                    updated_at = now()
                WHERE id = %s
            """, (json.dumps({"result": result}), task_id))
        else:
            execute("""
                UPDATE tasks
                SET status = 'DONE',
                    updated_at = now()
                WHERE id = %s
            """, (task_id,))


def handle_daily_update_all(task: dict) -> dict:
    """
    DAILY_UPDATE_ALL: Run full pipeline for all active tickers.

    Does NOT enqueue separate tasks - runs pipeline directly for each ticker.
    """
    print("\n" + "=" * 60)
    print("DAILY_UPDATE_ALL: Processing all active tickers")
    print("=" * 60)

    # Get active tickers
    tickers = fetch_all(
        "SELECT ticker FROM tracked_stocks WHERE is_active = true ORDER BY ticker"
    )

    if not tickers:
        print("No active tickers found!")
        return {"tickers_processed": 0, "results": {}}

    # Get params from payload or use defaults
    payload = task.get("payload", {})
    params = {**DAILY_PARAMS, **payload}

    results = {}
    for row in tickers:
        ticker = row["ticker"]
        try:
            result = run_pipeline_for_ticker(
                ticker=ticker,
                news_hours=params["news_hours"],
                score_limit=params["score_limit"],
                prices_days=params["prices_days"],
                agg_days=params["agg_days"],
                metrics_days=params["metrics_days"],
                window_days=params["window_days"],
            )
            results[ticker] = {
                "success": result["success"],
                "elapsed": result["elapsed_seconds"],
            }
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            results[ticker] = {"success": False, "error": str(e)}

    print("\n" + "=" * 60)
    print(f"DAILY_UPDATE_ALL COMPLETE: {len(results)} tickers processed")
    print("=" * 60)

    return {"tickers_processed": len(results), "results": results}


def handle_refresh_stock(task: dict) -> dict:
    """
    REFRESH_STOCK: Refresh data for a single ticker.

    Ticker comes from task.ticker or task.payload.ticker
    """
    ticker = task.get("ticker")
    if not ticker:
        ticker = task.get("payload", {}).get("ticker")

    if not ticker:
        raise ValueError("No ticker specified in task")

    print(f"\n{'='*60}")
    print(f"REFRESH_STOCK: {ticker}")
    print(f"{'='*60}")

    # Get params from payload or use defaults
    payload = task.get("payload", {})
    params = {**REFRESH_PARAMS, **payload}

    result = run_pipeline_for_ticker(
        ticker=ticker,
        news_hours=params.get("news_hours", REFRESH_PARAMS["news_hours"]),
        score_limit=params.get("score_limit", REFRESH_PARAMS["score_limit"]),
        prices_days=params.get("prices_days", REFRESH_PARAMS["prices_days"]),
        agg_days=params.get("agg_days", REFRESH_PARAMS["agg_days"]),
        metrics_days=params.get("metrics_days", REFRESH_PARAMS["metrics_days"]),
        window_days=params.get("window_days", REFRESH_PARAMS["window_days"]),
    )

    print(f"\n{'='*60}")
    print(f"REFRESH_STOCK COMPLETE: {ticker}")
    print(f"{'='*60}")

    return result


def handle_backfill_stock(task: dict) -> dict:
    """
    BACKFILL_STOCK: Full 30-day backfill for a single ticker.

    Uses larger limits for news_hours and score_limit, and computes
    metrics for multiple window sizes (7, 14, 30 days).
    """
    ticker = task.get("ticker")
    if not ticker:
        ticker = task.get("payload", {}).get("ticker")

    if not ticker:
        raise ValueError("No ticker specified in task")

    print(f"\n{'='*60}")
    print(f"BACKFILL_STOCK: {ticker}")
    print(f"{'='*60}")

    # Get params from payload or use backfill defaults
    payload = task.get("payload", {})
    params = {**BACKFILL_PARAMS, **payload}

    result = run_pipeline_for_ticker(
        ticker=ticker,
        news_hours=params.get("news_hours", BACKFILL_PARAMS["news_hours"]),
        score_limit=params.get("score_limit", BACKFILL_PARAMS["score_limit"]),
        prices_days=params.get("prices_days", BACKFILL_PARAMS["prices_days"]),
        agg_days=params.get("agg_days", BACKFILL_PARAMS["agg_days"]),
        metrics_days=params.get("metrics_days", BACKFILL_PARAMS["metrics_days"]),
        window_days_list=params.get("window_days_list", BACKFILL_PARAMS["window_days_list"]),
    )

    print(f"\n{'='*60}")
    print(f"BACKFILL_STOCK COMPLETE: {ticker}")
    print(f"{'='*60}")

    return result


def handle_backfill_defaults(task: dict) -> dict:
    """
    BACKFILL_DEFAULTS: Backfill all 5 default tickers.

    Runs full backfill pipeline for TSLA, NVDA, JPM, PFE, GME.
    """
    print(f"\n{'='*60}")
    print(f"BACKFILL_DEFAULTS: Processing {len(DEFAULT_TICKERS)} tickers")
    print(f"  Tickers: {', '.join(DEFAULT_TICKERS)}")
    print(f"{'='*60}")

    results = {}
    for ticker in DEFAULT_TICKERS:
        try:
            print(f"\n--- Backfilling {ticker} ---")
            result = run_pipeline_for_ticker(
                ticker=ticker,
                news_hours=BACKFILL_PARAMS["news_hours"],
                score_limit=BACKFILL_PARAMS["score_limit"],
                prices_days=BACKFILL_PARAMS["prices_days"],
                agg_days=BACKFILL_PARAMS["agg_days"],
                metrics_days=BACKFILL_PARAMS["metrics_days"],
                window_days_list=BACKFILL_PARAMS["window_days_list"],
            )
            results[ticker] = {
                "success": result.get("success", False),
                "elapsed": result.get("elapsed_seconds", 0),
            }
        except Exception as e:
            print(f"Error backfilling {ticker}: {e}")
            results[ticker] = {"success": False, "error": str(e)}

    print(f"\n{'='*60}")
    print(f"BACKFILL_DEFAULTS COMPLETE: {len(results)} tickers processed")
    print(f"{'='*60}")

    return {"tickers": DEFAULT_TICKERS, "results": results}


def run_once() -> bool:
    """
    Process one task and return.
    Returns True if a task was processed, False if no tasks available.
    """
    task = claim_next_task()
    if not task:
        return False

    task_id = task["id"]
    task_type = task["task_type"]
    attempts = task["attempts"]

    print(f"\n[WORKER] Processing: {task_type}")
    print(f"  Task ID: {task_id}")
    print(f"  Ticker: {task.get('ticker', 'N/A')}")
    print(f"  Attempt: {attempts}/{MAX_ATTEMPTS}")

    try:
        if task_type == "DAILY_UPDATE_ALL":
            result = handle_daily_update_all(task)
        elif task_type == "REFRESH_STOCK":
            result = handle_refresh_stock(task)
        elif task_type == "BACKFILL_STOCK":
            result = handle_backfill_stock(task)
        elif task_type == "BACKFILL_DEFAULTS":
            result = handle_backfill_defaults(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

        complete_task(task_id, result=result)
        print(f"\n[WORKER] ✓ Task {task_id} completed successfully")
        return True

    except Exception as e:
        error_msg = str(e)
        print(f"\n[WORKER] ✗ Task {task_id} failed: {error_msg}")

        if attempts >= MAX_ATTEMPTS:
            print(f"  Max attempts ({MAX_ATTEMPTS}) reached - marking as ERROR")
            complete_task(task_id, error=error_msg)
        else:
            # Leave as ERROR, manual retry needed
            complete_task(task_id, error=f"Attempt {attempts}: {error_msg}")

        return True


def run_loop(poll_interval: int = 10):
    """Continuously poll for tasks."""
    print("=" * 60)
    print("WORKER: Starting task loop")
    print(f"  Poll interval: {poll_interval}s")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    while True:
        try:
            if not run_once():
                print(f"[WORKER] No tasks, sleeping {poll_interval}s...")
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n[WORKER] Shutting down...")
            break
        except Exception as e:
            print(f"[WORKER] Error: {e}")
            time.sleep(poll_interval)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_once()
    else:
        run_loop()
