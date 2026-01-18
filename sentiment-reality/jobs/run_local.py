#!/usr/bin/env python3
"""
Local runner - run pipeline tasks without the task queue.

Usage:
  python run_local.py daily              - Run DAILY_UPDATE_ALL logic
  python run_local.py refresh TSLA       - Run REFRESH_STOCK logic for TSLA
  python run_local.py worker-once        - Poll and process ONE task from queue
  python run_local.py bootstrap          - Bootstrap default watchlist

This bypasses the task queue and runs directly, useful for:
- Testing pipeline changes
- Manual one-off runs
- Development/debugging
"""
import sys
from datetime import datetime

# Default parameters
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


def run_daily():
    """Run DAILY_UPDATE_ALL logic - process all active tickers."""
    from db import fetch_all, is_configured
    from pipeline import run_pipeline_for_ticker

    if not is_configured():
        print("ERROR: Database not configured. Set DATABASE_URL in .env")
        return False

    print("=" * 60)
    print("LOCAL RUN: DAILY_UPDATE_ALL")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    # Get active tickers
    tickers = fetch_all(
        "SELECT ticker FROM tracked_stocks WHERE is_active = true ORDER BY ticker"
    )

    if not tickers:
        print("\nNo active tickers found!")
        print("Run: python run_local.py bootstrap")
        return False

    print(f"\nActive tickers: {[t['ticker'] for t in tickers]}")

    results = {}
    for row in tickers:
        ticker = row["ticker"]
        try:
            result = run_pipeline_for_ticker(
                ticker=ticker,
                **DAILY_PARAMS,
            )
            results[ticker] = result["success"]
        except Exception as e:
            print(f"\nError processing {ticker}: {e}")
            results[ticker] = False

    # Summary
    print("\n" + "=" * 60)
    print("DAILY RUN COMPLETE")
    print("=" * 60)
    success_count = sum(1 for v in results.values() if v)
    print(f"Results: {success_count}/{len(results)} tickers succeeded")
    for ticker, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {ticker}")

    return all(results.values())


def run_refresh(ticker: str):
    """Run REFRESH_STOCK logic for a single ticker."""
    from db import is_configured
    from pipeline import run_pipeline_for_ticker

    if not is_configured():
        print("ERROR: Database not configured. Set DATABASE_URL in .env")
        return False

    ticker = ticker.upper()

    print("=" * 60)
    print(f"LOCAL RUN: REFRESH_STOCK {ticker}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    try:
        result = run_pipeline_for_ticker(
            ticker=ticker,
            **REFRESH_PARAMS,
        )

        print("\n" + "=" * 60)
        if result["success"]:
            print(f"✓ REFRESH COMPLETE: {ticker}")
        else:
            print(f"✗ REFRESH FAILED: {ticker}")
            if "error" in result:
                print(f"  Error: {result['error']}")
        print("=" * 60)

        return result["success"]

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_worker_once():
    """Poll and process ONE task from the queue."""
    from worker import run_once

    print("=" * 60)
    print("LOCAL RUN: WORKER-ONCE")
    print("=" * 60)

    processed = run_once()

    if processed:
        print("\n✓ Task processed")
    else:
        print("\nNo pending tasks found")

    return processed


def run_bootstrap():
    """Bootstrap default watchlist."""
    from bootstrap_watchlist import bootstrap_watchlist

    print("=" * 60)
    print("LOCAL RUN: BOOTSTRAP WATCHLIST")
    print("=" * 60)

    return bootstrap_watchlist()


def run_backfill_defaults():
    """Run full 30-day backfill for all default tickers."""
    from db import is_configured
    from pipeline import run_pipeline_for_ticker

    if not is_configured():
        print("ERROR: Database not configured. Set DATABASE_URL in .env")
        return False

    print("=" * 60)
    print("LOCAL RUN: BACKFILL DEFAULTS")
    print(f"Tickers: {', '.join(DEFAULT_TICKERS)}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    results = {}
    for ticker in DEFAULT_TICKERS:
        print(f"\n{'='*50}")
        print(f"Backfilling {ticker}...")
        print("=" * 50)
        try:
            result = run_pipeline_for_ticker(
                ticker=ticker,
                news_hours=BACKFILL_PARAMS["news_hours"],
                score_limit=BACKFILL_PARAMS["score_limit"],
                prices_days=BACKFILL_PARAMS["prices_days"],
                agg_days=BACKFILL_PARAMS["agg_days"],
                metrics_days=BACKFILL_PARAMS["metrics_days"],
                window_days_list=BACKFILL_PARAMS["window_days_list"],
            )
            results[ticker] = result["success"]
        except Exception as e:
            print(f"\nError backfilling {ticker}: {e}")
            results[ticker] = False

    # Summary
    print("\n" + "=" * 60)
    print("BACKFILL COMPLETE")
    print("=" * 60)
    success_count = sum(1 for v in results.values() if v)
    print(f"Results: {success_count}/{len(results)} tickers succeeded")
    for ticker, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {ticker}")

    return all(results.values())


def print_usage():
    """Print usage information."""
    print("""
Usage: python run_local.py <command> [args]

Commands:
  daily              Run DAILY_UPDATE_ALL for all active tickers
  refresh <TICKER>   Run REFRESH_STOCK for a single ticker
  worker-once        Poll and process ONE task from queue
  bootstrap          Bootstrap default watchlist (TSLA, NVDA, JPM, PFE, GME)
  backfill-defaults  Full 30-day backfill for all default tickers

Examples:
  python run_local.py daily
  python run_local.py refresh TSLA
  python run_local.py worker-once
  python run_local.py bootstrap
  python run_local.py backfill-defaults
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "daily":
        success = run_daily()
    elif command == "refresh":
        if len(sys.argv) < 3:
            print("ERROR: ticker required")
            print("Usage: python run_local.py refresh <TICKER>")
            sys.exit(1)
        ticker = sys.argv[2]
        success = run_refresh(ticker)
    elif command == "worker-once":
        success = run_worker_once()
    elif command == "bootstrap":
        success = run_bootstrap()
    elif command == "backfill-defaults":
        success = run_backfill_defaults()
    elif command in ["-h", "--help", "help"]:
        print_usage()
        sys.exit(0)
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
