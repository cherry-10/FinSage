from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime
from typing import List

import schemas
import auth
from database import get_db
from ai_service import generate_budget_plan, detect_anomalies

app = FastAPI(title="FinSage API", version="1.0.0")

# ============================================
# CORS
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://finsage.vercel.app",
        "https://finsage-smart-choice-app.vercel.app",
        "https://fin-sage-nks6.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Health
# ============================================
@app.get("/")
def health():
    return {"status": "healthy", "service": "FinSage API"}

@app.get("/api/health")
def detailed_health():
    try:
        db = get_db()
        # Test if users table exists
        result = db.table("users").select("id").limit(1).execute()
        return {
            "status": "healthy",
            "service": "FinSage API",
            "database": "connected",
            "users_table": "exists" if result.data else "empty"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "FinSage API",
            "database": "error",
            "error": str(e)
        }

# ============================================
# AUTH: REGISTER
# ============================================
@app.post("/api/auth/register", response_model=schemas.Token)
def register(
    user_data: schemas.UserCreate,
    db=Depends(get_db),
):
    # Check if user already exists
    existing_user = (
        db.table("users")
        .select("*")
        .eq("email", user_data.email)
        .execute()
    )
    
    if existing_user.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    password_hash = auth.hash_password(user_data.password)
    payload = {
        "name": user_data.name,
        "email": user_data.email,
        "phone": user_data.phone,
        "password_hash": password_hash,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    result = db.table("users").insert(payload).execute()
    user = result.data[0]
    
    # Create access token
    access_token = auth.create_access_token(
        data={"sub": user["email"], "id": user["id"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# ============================================
# AUTH: LOGIN
# ============================================
@app.post("/api/auth/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    result = (
        db.table("users")
        .select("*")
        .eq("email", form_data.username)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user = result.data[0]

    if not auth.verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = auth.create_access_token(
        data={"sub": user["email"], "id": user["id"]}
    )

    return {"access_token": access_token, "token_type": "bearer"}

# ============================================
# TRANSACTIONS: CREATE
# ============================================
@app.post("/api/transactions")
def create_transaction(
    tx: schemas.TransactionCreate,
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    payload = {
        "user_id": current_user["id"],
        "amount": abs(tx.amount),
        "category": tx.category,
        "description": tx.description,
        "transaction_type": tx.transaction_type,
        "transaction_date": (
            tx.transaction_date.isoformat()
            if tx.transaction_date
            else datetime.utcnow().isoformat()
        ),
    }

    db.table("transactions").insert(payload).execute()
    return {"message": "Transaction created successfully"}

# ============================================
# TRANSACTIONS: LIST
# ============================================
@app.get("/api/transactions", response_model=List[schemas.TransactionResponse])
def get_transactions(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    result = (
        db.table("transactions")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("transaction_date", desc=True)
        .execute()
    )

    return result.data
