"""Stock management endpoints - add stocks and trigger refresh tasks."""
from fastapi import APIRouter
from schemas import AddStockRequest, RefreshStockRequest, TaskResponse
from db import execute, is_configured

router = APIRouter()


@router.post("/stocks", response_model=TaskResponse)
def add_stock(request: AddStockRequest):
    """
    Add a stock to track.
    - Upserts into tracked_stocks
    - Creates a BACKFILL_STOCK task
    """
    ticker = request.ticker.upper()

    if not is_configured():
        # Return mock response when DB not configured
        return TaskResponse(queued=True, task_type="BACKFILL_STOCK", ticker=ticker)

    # Upsert into tracked_stocks
    execute("""
        INSERT INTO tracked_stocks (ticker, is_active)
        VALUES (%s, true)
        ON CONFLICT (ticker) DO UPDATE SET is_active = true
    """, (ticker,))

    # Create backfill task
    execute("""
        INSERT INTO tasks (task_type, ticker, priority, status)
        VALUES ('BACKFILL_STOCK', %s, 10, 'PENDING')
    """, (ticker,))

    return TaskResponse(queued=True, task_type="BACKFILL_STOCK", ticker=ticker)


@router.post("/stocks/refresh", response_model=TaskResponse)
def refresh_stock(request: RefreshStockRequest):
    """
    Trigger a refresh for a stock.
    - Creates a REFRESH_STOCK task with high priority
    """
    ticker = request.ticker.upper()

    if not is_configured():
        # Return mock response when DB not configured
        return TaskResponse(queued=True, task_type="REFRESH_STOCK", ticker=ticker)

    # Create refresh task (higher priority)
    execute("""
        INSERT INTO tasks (task_type, ticker, priority, status)
        VALUES ('REFRESH_STOCK', %s, 50, 'PENDING')
    """, (ticker,))

    return TaskResponse(queued=True, task_type="REFRESH_STOCK", ticker=ticker)
