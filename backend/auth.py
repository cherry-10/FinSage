from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import Client as SupabaseClient
from config import get_settings
from database import get_supabase_client

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# ============================================
# JWT Utilities
# ============================================
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SUPABASE_JWT_SECRET or settings.SECRET_KEY, 
        algorithm="HS256"
    )
    return encoded_jwt

# ============================================
# Current User Dependency (Supabase)
# ============================================
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    supabase: SupabaseClient = Depends(get_supabase_client)
) -> dict:
    """
    Get the current authenticated user from the JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify the JWT token
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET or settings.SECRET_KEY,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
            
        # Get user from Supabase
        response = supabase.auth.admin.get_user_by_id(user_id)
        if not response.user:
            raise credentials_exception
            
        return {
            "id": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata or {}
        }
        
    except JWTError:
        raise credentials_exception

async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get the current active user
    """
    # Add any additional checks here (e.g., user is active, not banned, etc.)
    return current_user
