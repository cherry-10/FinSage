from pydantic_settings import BaseSettings
from pydantic import field_validator, ValidationError
from functools import lru_cache
import os
from typing import Optional

class Settings(BaseSettings):
    """
    Production-ready configuration using Pydantic Settings.
    
    Environment variables are loaded from .env file (local) or 
    system environment (production/Render).
    """
    
    # ============================================
    # Supabase Configuration
    # ============================================
    SUPABASE_URL: str = "https://cgejzlbedvvdlusvrged.supabase.co"
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Database URL - MUST use Supabase Pooler for Render deployment
    # Format: postgresql://postgres.{ref}:{password}@aws-0-{region}.pooler.supabase.com:6543/postgres
    DATABASE_URL: str
    
    # ============================================
    # JWT Configuration
    # ============================================
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ============================================
    # AI Configuration
    # ============================================
    GROQ_API_KEY: str
    
    # ============================================
    # Application Configuration
    # ============================================
    APP_NAME: str = "FinSage API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # ============================================
    # Database Pool Configuration (Production)
    # ============================================
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
    DB_ECHO: bool = False
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Validate DATABASE_URL format for production deployment.
        
        Ensures:
        - Uses Supabase Pooler (not direct connection)
        - Uses correct port (6543 for transaction mode)
        - Has proper format
        """
        if not v:
            raise ValueError("DATABASE_URL is required")
        
        # Check if using pooler (recommended for Render)
        if "pooler.supabase.com" not in v:
            import warnings
            warnings.warn(
                "⚠️  Using direct connection (db.*.supabase.co). "
                "Consider using Supabase Pooler for better Render compatibility. "
                "Format: postgresql://postgres.{ref}:{password}@aws-0-{region}.pooler.supabase.com:6543/postgres"
            )
        
        # Check port
        if ":6543/" in v:
            # Transaction mode - optimal for FastAPI
            pass
        elif ":5432/" in v and "pooler.supabase.com" in v:
            # Session mode pooler - acceptable
            pass
        elif ":5432/" in v:
            # Direct connection - warn
            import warnings
            warnings.warn(
                "⚠️  Using direct connection on port 5432. "
                "May cause IPv6 issues on Render. "
                "Use pooler: postgresql://postgres.{ref}:{password}@aws-0-{region}.pooler.supabase.com:6543/postgres"
            )
        
        return v
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure SECRET_KEY is strong enough for production."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters for production")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are loaded only once
    and reused across the application.
    """
    try:
        return Settings()
    except ValidationError as e:
        print(f"❌ Configuration Error: {e}")
        raise
