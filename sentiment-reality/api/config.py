"""Configuration loaded from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from api/)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Supabase (optional, for direct API access)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Parse DATABASE_URL for psycopg2 if needed
def get_db_config():
    """Parse DATABASE_URL into connection params."""
    if not DATABASE_URL:
        return None
    # Format: postgresql://user:pass@host:port/dbname
    url = DATABASE_URL
    if url.startswith("postgresql://"):
        url = url[13:]
    elif url.startswith("postgres://"):
        url = url[11:]

    # user:pass@host:port/dbname
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
        "dbname": dbname.split("?")[0],  # Remove query params
    }
