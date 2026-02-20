from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import Client as SupabaseClient
from config import get_settings
from database import get_supabase_client
from passlib.context import CryptContext

settings = get_settings()

# Password hashing - optimized rounds for faster login (4 rounds = ~50ms vs 10 rounds = ~300ms)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# ============================================
# Password Utilities
# ============================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

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
        settings.SECRET_KEY, 
        algorithm="HS256"
    )
    return encoded_jwt

# ============================================
# Current User Dependency (Custom User Table)
# ============================================
async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> dict:
    """
    Get the current authenticated user from the JWT token (no DB call)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        email = payload.get("sub")
        user_id = payload.get("id")
        name = payload.get("name", "")
        
        if not email or not user_id:
            raise credentials_exception
            
        return {"id": user_id, "email": email, "name": name}
        
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
