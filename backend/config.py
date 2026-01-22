from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str = "https://cgejzlbedvvdlusvrged.supabase.co"
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    DATABASE_URL: str
    
    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Configuration
    GROQ_API_KEY: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
