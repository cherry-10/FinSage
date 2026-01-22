"""
Supabase database client for FastAPI + Render (FREE tier compatible).

- Uses Supabase Python client (HTTP-based)
- No direct PostgreSQL connections
- No DATABASE_URL
- No connection pooling issues
- Safe for Render Free (IPv4-only)
"""

import logging
from functools import lru_cache
from supabase import create_client, Client
from config import get_settings

# ============================================
# Logging
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================
# Supabase Client (Singleton)
# ============================================
@lru_cache()
def get_supabase_client() -> Client:
    """
    Create and cache Supabase client.
    Uses SERVICE ROLE KEY (backend only).
    """
    settings = get_settings()

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise RuntimeError("Supabase credentials are missing")

    logger.info("Initializing Supabase client")

    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )

# ============================================
# FastAPI Dependency
# ============================================
def get_db() -> Client:
    """
    Dependency for FastAPI routes.
    """
    return get_supabase_client()

# ============================================
# Health Check
# ============================================
def check_db_health() -> bool:
    """
    Simple Supabase connectivity check.
    """
    try:
        client = get_supabase_client()
        client.table("users").select("id").limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Supabase health check failed: {e}")
        return False
