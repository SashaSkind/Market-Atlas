"""Database connection helper for Postgres."""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import get_db_config

def is_configured() -> bool:
    """Check if database is configured."""
    return get_db_config() is not None

@contextmanager
def get_connection():
    """Get a database connection. Use as context manager."""
    config = get_db_config()
    if not config:
        raise RuntimeError("DATABASE_URL not configured")

    conn = psycopg2.connect(**config)
    try:
        yield conn
    finally:
        conn.close()

def query(sql: str, params: tuple = None) -> list[dict]:
    """Execute a SELECT query and return results as list of dicts."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

def execute(sql: str, params: tuple = None) -> int:
    """Execute an INSERT/UPDATE/DELETE and return affected row count."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount

def execute_returning(sql: str, params: tuple = None) -> dict | None:
    """Execute INSERT/UPDATE with RETURNING and return the row."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            conn.commit()
            row = cur.fetchone()
            return dict(row) if row else None
