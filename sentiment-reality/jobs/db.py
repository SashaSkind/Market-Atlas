"""Database helper for jobs."""
import os
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

# Load .env from project root (one level up from jobs/)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_db_config():
    """Parse DATABASE_URL into connection params."""
    if not DATABASE_URL:
        return None
    url = DATABASE_URL
    if url.startswith("postgresql://"):
        url = url[13:]
    elif url.startswith("postgres://"):
        url = url[11:]

    auth, rest = url.split("@")
    user, password = auth.split(":")
    host_port, dbname = rest.split("/")
    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host, port = host_port, "5432"

    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "dbname": dbname.split("?")[0],
    }


def is_configured() -> bool:
    """Check if database is configured."""
    return get_db_config() is not None


def get_conn():
    """Get a database connection (caller must close)."""
    config = get_db_config()
    if not config:
        raise RuntimeError("DATABASE_URL not configured. Set it in .env file.")
    return psycopg2.connect(**config)


@contextmanager
def get_connection():
    """Get a database connection as context manager."""
    conn = get_conn()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction():
    """Context manager for a transaction. Auto-commits on success, rolls back on error."""
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(sql: str, params: tuple = None) -> list[dict]:
    """Execute SELECT and return list of dicts."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


# Alias for compatibility
query = fetch_all


def execute(sql: str, params: tuple = None) -> int:
    """Execute INSERT/UPDATE/DELETE and return affected row count."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount


def execute_many(sql: str, params_list: list[tuple]) -> int:
    """Execute many INSERTs."""
    if not params_list:
        return 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, params_list)
            conn.commit()
            return cur.rowcount


# Alias for compatibility with spec
executemany = execute_many
