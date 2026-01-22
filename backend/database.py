"""
Production-ready database configuration for FastAPI + Supabase + Render.

This module configures SQLAlchemy with optimal settings for:
- Supabase Connection Pooler (Transaction Mode)
- Render deployment (IPv4 compatibility)
- Production connection pooling
- Automatic reconnection and health checks
"""

from sqlalchemy import create_engine, text, event, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from config import get_settings
import logging
from typing import Generator
from contextlib import contextmanager

# ============================================
# Logging Configuration
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# Load Settings
# ============================================
settings = get_settings()

# ============================================
# SQLAlchemy Engine Configuration
# ============================================

def create_db_engine():
    """
    Create SQLAlchemy engine with production-ready configuration.
    
    Optimized for:
    - Supabase Pooler (Transaction Mode - Port 6543)
    - Render deployment
    - Connection pooling and reuse
    - Automatic reconnection
    - SSL/TLS encryption
    """
    
    # Connection arguments for Supabase
    connect_args = {
        "connect_timeout": 10,           # Connection timeout in seconds
        "options": "-c timezone=utc",    # Set timezone to UTC
    }
    
    # Add SSL for production (Supabase requires SSL)
    if "supabase.co" in settings.DATABASE_URL:
        connect_args["sslmode"] = "require"
    
    engine = create_engine(
        settings.DATABASE_URL,
        
        # ============================================
        # Connection Pool Configuration
        # ============================================
        poolclass=QueuePool,                        # Use QueuePool for production
        pool_size=settings.DB_POOL_SIZE,            # Number of persistent connections (5)
        max_overflow=settings.DB_MAX_OVERFLOW,      # Additional connections when pool is full (10)
        pool_timeout=settings.DB_POOL_TIMEOUT,      # Timeout waiting for connection (30s)
        pool_recycle=settings.DB_POOL_RECYCLE,      # Recycle connections after 1 hour
        pool_pre_ping=settings.DB_POOL_PRE_PING,    # Test connection before using
        
        # ============================================
        # Performance & Debugging
        # ============================================
        echo=settings.DB_ECHO,                      # Log SQL queries (False in production)
        echo_pool=False,                            # Log pool checkouts (False in production)
        
        # ============================================
        # Connection Arguments
        # ============================================
        connect_args=connect_args,
        
        # ============================================
        # Execution Options
        # ============================================
        execution_options={
            "isolation_level": "READ COMMITTED"     # PostgreSQL default
        }
    )
    
    # ============================================
    # Event Listeners for Connection Management
    # ============================================
    
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log successful connections."""
        logger.debug("Database connection established")
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Verify connection is alive on checkout."""
        # pool_pre_ping handles this, but we log it
        logger.debug("Connection checked out from pool")
    
    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Log connection return to pool."""
        logger.debug("Connection returned to pool")
    
    return engine

# ============================================
# Initialize Engine
# ============================================
try:
    logger.info("Initializing database engine...")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'hidden'}")
    
    engine = create_db_engine()
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        logger.info(f"✅ Database connection successful")
        logger.info(f"PostgreSQL version: {version.split(',')[0]}")
        
        # Verify we're using pooler
        if "pooler.supabase.com" in settings.DATABASE_URL:
            logger.info("✅ Using Supabase Connection Pooler (Render-optimized)")
        else:
            logger.warning("⚠️  Not using Supabase Pooler - may have issues on Render")
    
except Exception as e:
    logger.error(f"❌ Database connection failed: {str(e)}")
    logger.error(f"Check your DATABASE_URL format:")
    logger.error(f"Expected: postgresql://postgres.{{ref}}:{{password}}@aws-0-{{region}}.pooler.supabase.com:6543/postgres")
    raise Exception(f"CRITICAL: Cannot connect to database. Error: {str(e)}")

# ============================================
# Session Configuration
# ============================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Don't expire objects after commit
)

# ============================================
# Declarative Base
# ============================================
Base = declarative_base()

# ============================================
# Dependency Injection for FastAPI
# ============================================
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Features:
    - Automatic session management
    - Rollback on error
    - Proper cleanup
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

# ============================================
# Context Manager for Manual Sessions
# ============================================
@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for manual database sessions.
    
    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database context error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

# ============================================
# Database Initialization
# ============================================
def init_db():
    """
    Initialize database tables.
    
    Creates all tables defined in models.
    Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).
    """
    try:
        logger.info("Creating/verifying database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified successfully")
        
        # Log table names
        table_names = Base.metadata.tables.keys()
        logger.info(f"Tables: {', '.join(table_names)}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database tables: {str(e)}")
        raise

# ============================================
# Health Check
# ============================================
def check_db_health() -> bool:
    """
    Check database connection health.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

# ============================================
# Cleanup
# ============================================
def dispose_engine():
    """
    Dispose of the engine and close all connections.
    
    Call this on application shutdown.
    """
    logger.info("Disposing database engine...")
    engine.dispose()
    logger.info("✅ Database engine disposed")
