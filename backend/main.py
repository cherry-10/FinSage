from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import List, Optional

import schemas
import auth
from database import get_db
from ai_service import generate_budget_plan, detect_anomalies
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import warnings
warnings.filterwarnings('ignore')

# Optional imports for forecasting - graceful fallback if not available
try:
    import pandas as pd
    import numpy as np
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    FORECASTING_AVAILABLE = True
except ImportError:
    FORECASTING_AVAILABLE = False
    print("statsmodels not available - using simple forecasting fallback")

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
    try:
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

# ============================================
# AUTH: LOGIN
# ============================================
@app.post("/api/auth/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    try:
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

# ============================================
# AUTH: FORGOT PASSWORD
# ============================================
@app.post("/api/auth/forgot-password")
def forgot_password(
    email: str,
    db=Depends(get_db),
):
    try:
        # Check if user exists
        result = (
            db.table("users")
            .select("id, email")
            .eq("email", email)
            .execute()
        )
        
        if not result.data:
            # Don't reveal if email exists or not for security
            return {"message": "If the email exists, a password reset link has been sent."}
        
        user = result.data[0]
        
        # Generate reset token (valid for 1 hour)
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Store reset token in database
        db.table("password_resets").insert({
            "user_id": user["id"],
            "token": reset_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        # Send email with reset link
        reset_link = f"https://fin-sage-nks6.vercel.app/reset-password?token={reset_token}"
        send_reset_email(user["email"], reset_link)
        
        return {"message": "If the email exists, a password reset link has been sent."}
    
    except Exception as e:
        print(f"Forgot password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )

# ============================================
# AUTH: DIRECT PASSWORD RESET (no token needed)
# ============================================
@app.post("/api/auth/direct-reset-password")
def direct_reset_password(
    email: str,
    new_password: str,
    db=Depends(get_db),
):
    try:
        # Find user by email
        result = (
            db.table("users")
            .select("id, email")
            .eq("email", email)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address"
            )

        user = result.data[0]

        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )

        new_password_hash = auth.hash_password(new_password)

        db.table("users").update({
            "password_hash": new_password_hash
        }).eq("id", user["id"]).execute()

        return {"message": "Password has been reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Direct reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

# ============================================
# AUTH: RESET PASSWORD
# ============================================
@app.post("/api/auth/reset-password")
def reset_password(
    token: str,
    new_password: str,
    db=Depends(get_db),
):
    try:
        # Find valid reset token
        result = (
            db.table("password_resets")
            .select("*")
            .eq("token", token)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        reset_record = result.data[0]
        
        # Check if token is expired
        expires_at = datetime.fromisoformat(reset_record["expires_at"].replace("Z", "+00:00"))
        if datetime.utcnow() > expires_at.replace(tzinfo=None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Hash new password
        new_password_hash = auth.hash_password(new_password)
        
        # Update user password
        db.table("users").update({
            "password_hash": new_password_hash
        }).eq("id", reset_record["user_id"]).execute()
        
        # Delete used reset token
        db.table("password_resets").delete().eq("token", token).execute()
        
        return {"message": "Password has been reset successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

# ============================================
# EMAIL UTILITY
# ============================================
def send_reset_email(to_email: str, reset_link: str):
    """Send password reset email"""
    try:
        # Email configuration (using Gmail SMTP)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "charanteja1039@gmail.com"
        sender_password = "your_app_password"  # Use App Password, not regular password
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "FinSage - Password Reset Request"
        message["From"] = sender_email
        message["To"] = to_email
        
        # Email body
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #3b82f6;">Password Reset Request</h2>
              <p>You requested to reset your password for your FinSage account.</p>
              <p>Click the button below to reset your password:</p>
              <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" 
                   style="background-color: #3b82f6; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                  Reset Password
                </a>
              </div>
              <p style="color: #666; font-size: 14px;">
                This link will expire in 1 hour. If you didn't request this, please ignore this email.
              </p>
              <p style="color: #666; font-size: 14px;">
                Or copy and paste this link into your browser:<br>
                <a href="{reset_link}" style="color: #3b82f6;">{reset_link}</a>
              </p>
              <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
              <p style="color: #999; font-size: 12px; text-align: center;">
                FinSage - Personal Finance Management<br>
                This is an automated email, please do not reply.
              </p>
            </div>
          </body>
        </html>
        """
        
        part = MIMEText(html, "html")
        message.attach(part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
        
        print(f"Password reset email sent to {to_email}")
    
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        # Don't raise exception - we don't want to reveal email sending failures

# ============================================
# AUTH: GET CURRENT USER
# ============================================
@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    """Get current authenticated user information"""
    try:
        result = (
            db.table("users")
            .select("*")
            .eq("id", current_user["id"])
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return result.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}"
        )

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

# ============================================
# TRANSACTIONS: DELETE
# ============================================
@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        # Verify transaction belongs to user
        result = (
            db.table("transactions")
            .select("*")
            .eq("id", transaction_id)
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Delete transaction
        db.table("transactions").delete().eq("id", transaction_id).execute()
        
        return {"message": "Transaction deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete transaction: {str(e)}"
        )

# ============================================
# INCOME: CREATE
# ============================================
@app.post("/api/income", response_model=schemas.IncomeResponse)
def create_income(
    income_data: schemas.IncomeCreate,
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        payload = {
            "user_id": current_user["id"],
            "monthly_income": income_data.monthly_income,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = db.table("income").insert(payload).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create income record"
            )
        
        return result.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create income: {str(e)}"
        )

# ============================================
# INCOME: GET LATEST
# ============================================
@app.get("/api/income/latest", response_model=schemas.IncomeResponse)
def get_latest_income(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        result = (
            db.table("income")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No income record found"
            )
        
        return result.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch income: {str(e)}"
        )

# ============================================
# EXPENSE LIMITS: CREATE
# ============================================
@app.post("/api/expense-limits", response_model=schemas.ExpenseLimitResponse)
def create_expense_limit(
    limit_data: schemas.ExpenseLimitCreate,
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        payload = {
            "user_id": current_user["id"],
            "monthly_limit": limit_data.monthly_limit,
            "target_savings": limit_data.target_savings,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = db.table("expense_limits").insert(payload).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create expense limit"
            )
        
        return result.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create expense limit: {str(e)}"
        )

# ============================================
# EXPENSE LIMITS: GET LATEST
# ============================================
@app.get("/api/expense-limits/latest", response_model=schemas.ExpenseLimitResponse)
def get_latest_expense_limit(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        result = (
            db.table("expense_limits")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No expense limit found"
            )
        
        return result.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch expense limit: {str(e)}"
        )

# ============================================
# BUDGET: GENERATE
# ============================================
@app.post("/api/budget/generate")
def generate_budget(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        # Get latest income
        income_result = (
            db.table("income")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        # Get user's annual salary as fallback
        user_result = (
            db.table("users")
            .select("annual_salary")
            .eq("id", current_user["id"])
            .execute()
        )
        
        # Determine income
        income = None
        if income_result.data and income_result.data[0].get("monthly_income"):
            income = income_result.data[0]["monthly_income"]
        elif user_result.data and user_result.data[0].get("annual_salary"):
            income = float(user_result.data[0]["annual_salary"]) / 12
        
        if not income:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please set your annual salary in Profile settings first"
            )
        
        # Get latest expense limit
        limit_result = (
            db.table("expense_limits")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        # Use 80% of income as default expense limit if not set
        expense_limit = None
        if limit_result.data and limit_result.data[0].get("monthly_limit"):
            expense_limit = limit_result.data[0]["monthly_limit"]
        else:
            expense_limit = income * 0.8  # Default to 80% of income
        
        # Calculate target savings (20% of income or income - expense_limit)
        target_savings = income - expense_limit
        
        # Get user transactions for AI analysis
        transactions_result = (
            db.table("transactions")
            .select("*")
            .eq("user_id", current_user["id"])
            .limit(50)
            .execute()
        )
        
        # Prepare past expenses from transactions
        past_expenses = {}
        if transactions_result.data:
            for t in transactions_result.data:
                if t.get("transaction_type") == "expense":
                    category = t.get("category", "Other")
                    amount = t.get("amount", 0)
                    past_expenses[category] = past_expenses.get(category, 0) + amount
        
        # Generate budget using AI with correct parameters
        budget_categories = generate_budget_plan(
            income=income,
            target_savings=target_savings,
            past_expenses=past_expenses,
            loan_commitments=0  # Can be extended later
        )
        
        # Convert list of dicts to dict for storage
        budget_plan = {cat["category"]: cat["allocated_amount"] for cat in budget_categories}
        
        # Store budget plan
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        # Delete existing budget for current month
        db.table("budget_plans").delete().eq("user_id", current_user["id"]).eq("month", current_month).execute()
        
        # Insert new budget plans
        budget_records = []
        for category, amount in budget_plan.items():
            payload = {
                "user_id": current_user["id"],
                "month": current_month,
                "category": category,
                "allocated_amount": amount,
                "created_at": datetime.utcnow().isoformat()
            }
            budget_records.append(payload)
        
        if budget_records:
            db.table("budget_plans").insert(budget_records).execute()
        
        return {"message": "Budget generated successfully", "budget": budget_plan}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate budget: {str(e)}"
        )

# ============================================
# BUDGET: GET ALL
# ============================================
@app.get("/api/budget", response_model=List[schemas.BudgetPlanResponse])
def get_budget(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        result = (
            db.table("budget_plans")
            .select("*")
            .eq("user_id", current_user["id"])
            .eq("month", current_month)
            .execute()
        )
        
        return result.data if result.data else []
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch budget: {str(e)}"
        )

# ============================================
# BUDGET: SUMMARY (allocated vs actual)
# ============================================
@app.get("/api/budget/summary")
def get_budget_summary(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        current_month = datetime.utcnow().strftime("%Y-%m")
        now = datetime.utcnow()

        # Get budget allocations for current month
        budget_result = (
            db.table("budget_plans")
            .select("*")
            .eq("user_id", current_user["id"])
            .eq("month", current_month)
            .execute()
        )

        # Get all transactions for current month
        transactions_result = (
            db.table("transactions")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )

        # Filter current month expense transactions
        current_month_expenses = {}
        for t in (transactions_result.data or []):
            if t.get("transaction_type") != "expense":
                continue
            try:
                date = datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00"))
                if date.month == now.month and date.year == now.year:
                    cat = t.get("category", "Other")
                    current_month_expenses[cat] = current_month_expenses.get(cat, 0) + t["amount"]
            except Exception:
                continue

        budget_data = budget_result.data or []
        total_allocated = sum(b["allocated_amount"] for b in budget_data)
        total_spent = sum(current_month_expenses.values())

        categories = []
        for b in budget_data:
            cat = b["category"]
            allocated = b["allocated_amount"]
            spent = current_month_expenses.get(cat, 0)
            categories.append({
                "category": cat,
                "allocated_amount": allocated,
                "spent": spent,
                "remaining": allocated - spent,
                "percent_used": round((spent / allocated * 100), 1) if allocated > 0 else 0
            })

        return {
            "month": current_month,
            "total_allocated": total_allocated,
            "total_spent": total_spent,
            "total_remaining": total_allocated - total_spent,
            "categories": categories
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch budget summary: {str(e)}"
        )

# ============================================
# ANOMALIES: DETECT
# ============================================
@app.post("/api/anomalies/detect")
def detect_anomalies_endpoint(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        # Get user transactions
        transactions_result = (
            db.table("transactions")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        # Get expense limit
        limit_result = (
            db.table("expense_limits")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        expense_limit = limit_result.data[0]["monthly_limit"] if limit_result.data else None
        
        # Detect anomalies using AI
        anomalies = detect_anomalies(
            transactions=transactions_result.data,
            expense_limit=expense_limit
        )
        
        # Delete old anomalies
        db.table("anomalies").delete().eq("user_id", current_user["id"]).execute()
        
        # Store new anomalies
        if anomalies:
            anomaly_records = []
            for anomaly in anomalies:
                payload = {
                    "user_id": current_user["id"],
                    "category": anomaly.get("category", "General"),
                    "issue": anomaly.get("issue", ""),
                    "impact_amount": anomaly.get("impact_amount", 0.0),
                    "recommendation": anomaly.get("recommendation", ""),
                    "created_at": datetime.utcnow().isoformat()
                }
                anomaly_records.append(payload)
            
            db.table("anomalies").insert(anomaly_records).execute()
        
        return {"message": "Anomalies detected successfully", "count": len(anomalies)}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect anomalies: {str(e)}"
        )

# ============================================
# ANOMALIES: GET ALL
# ============================================
@app.get("/api/anomalies", response_model=List[schemas.AnomalyResponse])
def get_anomalies(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        result = (
            db.table("anomalies")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .execute()
        )
        
        return result.data if result.data else []
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch anomalies: {str(e)}"
        )

# ============================================
# DASHBOARD: GET STATS
# ============================================
@app.get("/api/dashboard")
def get_dashboard_stats(
    period: str = "current_month",
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        # Get user's annual salary for monthly income calculation
        user_result = (
            db.table("users")
            .select("annual_salary")
            .eq("id", current_user["id"])
            .execute()
        )
        
        monthly_income = 0
        if user_result.data and user_result.data[0].get("annual_salary"):
            annual_salary = float(user_result.data[0]["annual_salary"])
            monthly_income = annual_salary / 12
        
        print(f"User annual_salary: {user_result.data[0].get('annual_salary') if user_result.data else 'No data'}, Monthly income: {monthly_income}")
        
        # Get all transactions
        transactions_result = (
            db.table("transactions")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        transactions = transactions_result.data if transactions_result.data else []
        
        # Calculate stats based on period filter
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        last_month = current_month - 1 if current_month > 1 else 12
        last_month_year = current_year if current_month > 1 else current_year - 1
        
        # Determine which month to show based on period parameter
        if period == "all_time":
            # For all time, use all transactions
            selected_month_transactions = transactions
            # Calculate total income from all income transactions
            try:
                income_from_transactions = sum(
                    t["amount"] for t in transactions 
                    if t.get("transaction_type") == "income"
                )
                print(f"All Time - Income from transactions: {income_from_transactions}")
            except Exception as e:
                print(f"Error calculating income from transactions: {str(e)}")
                income_from_transactions = 0
            
            # Count unique months with ANY transactions (income or expense)
            unique_months = set()
            for t in transactions:
                try:
                    date = datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00"))
                    unique_months.add((date.year, date.month))
                except Exception as e:
                    print(f"Error parsing date for unique months: {str(e)}")
                    continue
            
            num_months = len(unique_months) if unique_months else 1
            print(f"All Time - Unique months with data: {num_months}")
            print(f"All Time - Monthly income from salary: {monthly_income}")
            
            # Calculate income: salary × months + positive income transactions
            salary_income = monthly_income * num_months if monthly_income > 0 else 0
            total_income = salary_income + income_from_transactions
            
            print(f"All Time - Salary income: {salary_income} ({monthly_income} × {num_months} months)")
            print(f"All Time - Positive transactions: {income_from_transactions}")
            print(f"All Time - Total income: {total_income}")
        elif period == "last_month":
            selected_month = last_month
            selected_year = last_month_year
            # Filter transactions for last month only
            selected_month_transactions = []
            for t in transactions:
                try:
                    date = datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00"))
                    if date.month == selected_month and date.year == selected_year:
                        selected_month_transactions.append(t)
                except Exception as e:
                    print(f"Error parsing transaction date for last month: {t.get('transaction_date')}, error: {str(e)}")
                    continue
            total_income = monthly_income
        else:  # current_month or default
            selected_month = current_month
            selected_year = current_year
            # Filter transactions for current month only
            selected_month_transactions = []
            for t in transactions:
                try:
                    date = datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00"))
                    if date.month == selected_month and date.year == selected_year:
                        selected_month_transactions.append(t)
                except Exception as e:
                    print(f"Error parsing transaction date for current month: {t.get('transaction_date')}, error: {str(e)}")
                    continue
            total_income = monthly_income
        
        # Calculate expenses for SELECTED period
        try:
            total_expenses = sum(
                t["amount"] for t in selected_month_transactions 
                if t.get("transaction_type") == "expense"
            )
        except Exception as e:
            print(f"Error calculating total expenses: {str(e)}")
            total_expenses = 0
        
        # Calculate this month and last month for comparison
        try:
            this_month_expenses = sum(
                t["amount"] for t in transactions 
                if t.get("transaction_type") == "expense" and 
                datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).month == current_month and
                datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).year == current_year
            )
        except Exception as e:
            print(f"Error calculating this month expenses: {str(e)}")
            this_month_expenses = 0
        
        try:
            last_month_expenses = sum(
                t["amount"] for t in transactions 
                if t.get("transaction_type") == "expense" and 
                datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).month == last_month and
                datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).year == last_month_year
            )
        except Exception as e:
            print(f"Error calculating last month expenses: {str(e)}")
            last_month_expenses = 0
        
        # Get anomaly count
        # Get current month anomalies (budget overruns)
        try:
            # Check for budget overruns in current month
            budget_result = (
                db.table("budget_plans")
                .select("*")
                .eq("user_id", current_user["id"])
                .eq("month", datetime.utcnow().strftime("%Y-%m"))
                .execute()
            )
            
            anomaly_count = 0
            if budget_result.data:
                # Calculate current month expenses by category
                current_month_expenses_by_cat = {}
                for t in transactions:
                    if t["transaction_type"] == "expense":
                        try:
                            date = datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00"))
                            if date.month == current_month and date.year == current_year:
                                category = t["category"]
                                current_month_expenses_by_cat[category] = current_month_expenses_by_cat.get(category, 0) + t["amount"]
                        except:
                            continue
                
                # Count budget overruns
                for budget in budget_result.data:
                    category = budget["category"]
                    allocated = budget["allocated_amount"]
                    spent = current_month_expenses_by_cat.get(category, 0)
                    if spent > allocated:
                        anomaly_count += 1
        except Exception as e:
            print(f"Error calculating anomaly count: {str(e)}")
            anomaly_count = 0
        
        # Get recent transactions for selected month
        recent_transactions = sorted(
            selected_month_transactions,
            key=lambda x: x["transaction_date"],
            reverse=True
        )[:5]
        
        # Calculate category breakdown for selected month only
        category_totals = {}
        for t in selected_month_transactions:
            if t["transaction_type"] == "expense":
                category = t["category"]
                category_totals[category] = category_totals.get(category, 0) + t["amount"]
        
        category_breakdown = [
            {"category": cat, "total": total}
            for cat, total in category_totals.items()
        ]
        
        savings = total_income - total_expenses
        print(f"Dashboard Stats - Period: {period}, Income: {total_income}, Expenses: {total_expenses}, Savings: {savings}")
        
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "savings": savings,
            "anomaly_count": anomaly_count,
            "last_month_expenses": last_month_expenses,
            "this_month_expenses": this_month_expenses,
            "recent_transactions": recent_transactions,
            "category_breakdown": category_breakdown
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard stats: {str(e)}"
        )

# ============================================
# DASHBOARD: GET TRENDS
# ============================================
@app.get("/api/dashboard/trends")
def get_dashboard_trends(
    period: str = "current_month",
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        from collections import defaultdict
        
        # Get transactions
        transactions_result = (
            db.table("transactions")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        transactions = transactions_result.data if transactions_result.data else []
        
        # Get current month and year
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        # Calculate last month
        last_month = current_month - 1 if current_month > 1 else 12
        last_month_year = current_year if current_month > 1 else current_year - 1
        
        # Filter transactions by month with error handling
        this_month_transactions = []
        last_month_transactions = []
        
        for t in transactions:
            try:
                if t["transaction_type"] == "expense":
                    date = datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00"))
                    if date.month == current_month and date.year == current_year:
                        this_month_transactions.append(t)
                    elif date.month == last_month and date.year == last_month_year:
                        last_month_transactions.append(t)
            except Exception as e:
                print(f"Error parsing transaction date in trends: {t.get('transaction_date')}, error: {str(e)}")
                continue
        
        # Calculate daily trends for this month
        this_month_daily = defaultdict(float)
        for t in this_month_transactions:
            date = datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).strftime("%d")
            this_month_daily[date] += t["amount"]
        
        this_month_daily_data = [
            {"date": date, "total": total}
            for date, total in sorted(this_month_daily.items())
        ]
        
        # Calculate daily trends for last month
        last_month_daily = defaultdict(float)
        for t in last_month_transactions:
            date = datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).strftime("%d")
            last_month_daily[date] += t["amount"]
        
        last_month_daily_data = [
            {"date": date, "total": total}
            for date, total in sorted(last_month_daily.items())
        ]
        
        # Calculate category breakdown for this month
        this_month_categories = defaultdict(float)
        for t in this_month_transactions:
            this_month_categories[t["category"]] += t["amount"]
        
        this_month_categories_data = [
            {"category": cat, "total": total}
            for cat, total in this_month_categories.items()
        ]
        
        # Calculate category breakdown for last month
        last_month_categories = defaultdict(float)
        for t in last_month_transactions:
            last_month_categories[t["category"]] += t["amount"]
        
        last_month_categories_data = [
            {"category": cat, "total": total}
            for cat, total in last_month_categories.items()
        ]
        
        # Calculate all-time monthly trends if period is all_time
        all_time_monthly_expenses = []
        all_time_monthly_savings = []
        
        if period == "all_time":
            try:
                # Get user's annual salary for income calculation
                monthly_income_salary = 0
                try:
                    user_result = (
                        db.table("users")
                        .select("annual_salary")
                        .eq("id", current_user["id"])
                        .execute()
                    )
                    
                    if user_result.data and len(user_result.data) > 0 and user_result.data[0].get("annual_salary"):
                        annual_salary = float(user_result.data[0]["annual_salary"])
                        monthly_income_salary = annual_salary / 12
                except Exception as db_error:
                    print(f"Error fetching user salary: {str(db_error)}")
                    monthly_income_salary = 0
                
                # Group all transactions by month-year
                monthly_data = defaultdict(lambda: {"expenses": 0, "income": 0})
                
                for t in transactions:
                    try:
                        date = datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00"))
                        month_key = date.strftime("%b %Y")  # e.g., "Jan 2024"
                        
                        if t["transaction_type"] == "expense":
                            monthly_data[month_key]["expenses"] += t["amount"]
                        elif t["transaction_type"] == "income":
                            monthly_data[month_key]["income"] += t["amount"]
                    except Exception as date_error:
                        print(f"Error parsing transaction date: {t.get('transaction_date')}, error: {str(date_error)}")
                        continue
                
                # Sort by date and create chart data - handle empty data
                if monthly_data:
                    try:
                        sorted_months = sorted(monthly_data.items(), key=lambda x: datetime.strptime(x[0], "%b %Y"))
                    except Exception as sort_error:
                        print(f"Error sorting months: {str(sort_error)}")
                        sorted_months = list(monthly_data.items())
                    
                    all_time_monthly_expenses = [
                        {"month": month, "total": data["expenses"]}
                        for month, data in sorted_months
                    ]
                    
                    # For savings, use actual income transactions or monthly salary if no income transactions
                    all_time_monthly_savings = [
                        {
                            "month": month, 
                            "savings": (data["income"] if data["income"] > 0 else monthly_income_salary) - data["expenses"]
                        }
                        for month, data in sorted_months
                    ]
                else:
                    all_time_monthly_expenses = []
                    all_time_monthly_savings = []
            except Exception as all_time_error:
                print(f"Error calculating all time trends: {str(all_time_error)}")
                all_time_monthly_expenses = []
                all_time_monthly_savings = []
        
        return {
            "this_month_daily": this_month_daily_data,
            "last_month_daily": last_month_daily_data,
            "this_month_categories": this_month_categories_data,
            "last_month_categories": last_month_categories_data,
            "all_time_monthly_expenses": all_time_monthly_expenses,
            "all_time_monthly_savings": all_time_monthly_savings
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trends: {str(e)}"
        )

# ============================================
# SETTINGS: GET
# ============================================
@app.get("/api/settings", response_model=schemas.UserSettingsResponse)
def get_settings(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        result = (
            db.table("user_settings")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        if not result.data:
            # Create default settings
            payload = {
                "user_id": current_user["id"],
                "notifications_enabled": True,
                "dark_mode": False,
                "anomaly_alerts": True
            }
            
            create_result = db.table("user_settings").insert(payload).execute()
            return create_result.data[0]
        
        return result.data[0]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch settings: {str(e)}"
        )

# ============================================
# SETTINGS: UPDATE
# ============================================
@app.put("/api/settings", response_model=schemas.UserSettingsResponse)
def update_settings(
    settings_data: schemas.UserSettingsUpdate,
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        # Get existing settings
        result = (
            db.table("user_settings")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        update_data = settings_data.model_dump(exclude_unset=True)
        
        if not result.data:
            # Create new settings
            payload = {
                "user_id": current_user["id"],
                "notifications_enabled": update_data.get("notifications_enabled", True),
                "dark_mode": update_data.get("dark_mode", False),
                "anomaly_alerts": update_data.get("anomaly_alerts", True)
            }
            
            create_result = db.table("user_settings").insert(payload).execute()
            return create_result.data[0]
        else:
            # Update existing settings
            settings_id = result.data[0]["id"]
            
            update_result = (
                db.table("user_settings")
                .update(update_data)
                .eq("id", settings_id)
                .execute()
            )
            
            return update_result.data[0]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}"
        )

# ============================================
# PROFILE: UPDATE
# ============================================
@app.put("/api/auth/me", response_model=schemas.UserResponse)
def update_profile(
    user_data: dict,
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        # Update user profile
        update_data = {}
        
        if "name" in user_data:
            update_data["name"] = user_data["name"]
        if "phone" in user_data:
            update_data["phone"] = user_data["phone"]
        if "profile_photo" in user_data:
            update_data["profile_photo"] = user_data["profile_photo"]
        if "annual_salary" in user_data:
            update_data["annual_salary"] = user_data["annual_salary"]
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        result = (
            db.table("users")
            .update(update_data)
            .eq("id", current_user["id"])
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return result.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

# ============================================
# PREDICT: EXPENSE FORECASTING
# ============================================
@app.get("/api/predict-expense")
def predict_expense(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        # Get all user transactions
        transactions_result = (
            db.table("transactions")
            .select("*")
            .eq("user_id", current_user["id"])
            .eq("transaction_type", "expense")
            .execute()
        )
        
        transactions = transactions_result.data if transactions_result.data else []
        
        if not transactions:
            return {
                "predicted_month": (datetime.utcnow() + timedelta(days=30)).strftime("%B %Y"),
                "predicted_amount": 0,
                "confidence_range": {"lower": 0, "upper": 0},
                "historical_data": [],
                "insight": "No transaction history available. Start adding expenses to get predictions.",
                "method": "none"
            }
        
        # Aggregate expenses by month
        monthly_expenses = {}
        for t in transactions:
            try:
                date = datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00"))
                month_key = date.strftime("%Y-%m")
                monthly_expenses[month_key] = monthly_expenses.get(month_key, 0) + t["amount"]
            except Exception as e:
                print(f"Error parsing transaction date: {str(e)}")
                continue
        
        if not monthly_expenses:
            return {
                "predicted_month": (datetime.utcnow() + timedelta(days=30)).strftime("%B %Y"),
                "predicted_amount": 0,
                "confidence_range": {"lower": 0, "upper": 0},
                "historical_data": [],
                "insight": "Unable to process transaction data.",
                "method": "none"
            }
        
        # Sort months chronologically
        sorted_months = sorted(monthly_expenses.items())
        num_months = len(sorted_months)
        
        # Prepare historical data for response
        historical_data = [
            {"month": datetime.strptime(month, "%Y-%m").strftime("%b %Y"), "amount": amount}
            for month, amount in sorted_months
        ]
        
        # Get next month
        last_month_date = datetime.strptime(sorted_months[-1][0], "%Y-%m")
        next_month_date = last_month_date + timedelta(days=32)
        next_month_date = next_month_date.replace(day=1)
        predicted_month = next_month_date.strftime("%B %Y")
        
        # METHOD 1: Less than 1 month - Use daily average projection
        if num_months < 1:
            # Calculate total days with transactions
            total_expenses = sum(monthly_expenses.values())
            
            # Get date range
            first_date = datetime.strptime(sorted_months[0][0], "%Y-%m")
            last_date = datetime.strptime(sorted_months[-1][0], "%Y-%m")
            days_span = (last_date - first_date).days + 30  # Add 30 for the month itself
            
            if days_span > 0:
                daily_avg = total_expenses / days_span
                predicted_amount = daily_avg * 30  # Project for 30 days
            else:
                predicted_amount = total_expenses
            
            # Simple confidence range (±20%)
            confidence_range = {
                "lower": predicted_amount * 0.8,
                "upper": predicted_amount * 1.2
            }
            
            # Calculate insight
            last_month_amount = sorted_months[-1][1]
            change_percent = ((predicted_amount - last_month_amount) / last_month_amount * 100) if last_month_amount > 0 else 0
            
            if change_percent > 10:
                insight = f"Predicted to increase by {abs(change_percent):.1f}% compared to last month. Based on daily average spending pattern."
            elif change_percent < -10:
                insight = f"Predicted to decrease by {abs(change_percent):.1f}% compared to last month. Based on daily average spending pattern."
            else:
                insight = f"Predicted to remain stable compared to last month. Based on daily average spending pattern."
            
            return {
                "predicted_month": predicted_month,
                "predicted_amount": round(predicted_amount, 2),
                "confidence_range": {
                    "lower": round(confidence_range["lower"], 2),
                    "upper": round(confidence_range["upper"], 2)
                },
                "historical_data": historical_data,
                "insight": insight,
                "method": "daily_average"
            }
        
        # METHOD 2: 1 or more months - ML forecast
        else:
            last_month_amount = sorted_months[-1][1]

            if FORECASTING_AVAILABLE and num_months >= 2:
                # Use Holt-Winters Exponential Smoothing (pure Python, no Stan)
                amounts = [amt for _, amt in sorted_months]
                series = np.array(amounts, dtype=float)
                if len(series) >= 3:
                    model = ExponentialSmoothing(series, trend='add', seasonal=None)
                else:
                    model = ExponentialSmoothing(series, trend=None, seasonal=None)
                fit = model.fit(optimized=True)
                predicted_amount = max(0, float(fit.forecast(1)[0]))
                hist_std = float(np.std(series)) if len(series) > 1 else predicted_amount * 0.15
                confidence_range = {
                    "lower": max(0, predicted_amount - hist_std),
                    "upper": predicted_amount + hist_std
                }
                method = "ai_forecast"
            elif num_months == 1:
                # Only 1 month — project same amount with ±15% range
                predicted_amount = last_month_amount
                confidence_range = {
                    "lower": predicted_amount * 0.85,
                    "upper": predicted_amount * 1.15
                }
                method = "weighted_average"
            else:
                # Fallback: weighted average (recent months weighted more)
                amounts = [amt for _, amt in sorted_months]
                n = len(amounts)
                weights = list(range(1, n + 1))  # 1,2,3... most recent = highest weight
                predicted_amount = sum(w * a for w, a in zip(weights, amounts)) / sum(weights)
                predicted_amount = max(0, predicted_amount)
                confidence_range = {
                    "lower": predicted_amount * 0.85,
                    "upper": predicted_amount * 1.15
                }
                method = "weighted_average"

            change_percent = ((predicted_amount - last_month_amount) / last_month_amount * 100) if last_month_amount > 0 else 0

            if change_percent > 10:
                insight = f"Predicted a {abs(change_percent):.1f}% increase in expenses next month. Consider reviewing your budget allocations."
            elif change_percent < -10:
                insight = f"Predicted a {abs(change_percent):.1f}% decrease in expenses next month. Great job managing your spending!"
            else:
                insight = f"Expenses predicted to remain stable next month, similar to your recent spending pattern."

            # Store prediction (optional, ignore errors)
            try:
                db.table("predictions").insert({
                    "user_id": current_user["id"],
                    "month": next_month_date.strftime("%Y-%m"),
                    "predicted_amount": round(predicted_amount, 2),
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            except Exception:
                pass

            return {
                "predicted_month": predicted_month,
                "predicted_amount": round(predicted_amount, 2),
                "confidence_range": {
                    "lower": round(confidence_range["lower"], 2),
                    "upper": round(confidence_range["upper"], 2)
                },
                "historical_data": historical_data,
                "insight": insight,
                "method": method
            }
    
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate expense prediction: {str(e)}"
        )

# ============================================
# AUTH: CHANGE PASSWORD
# ============================================
@app.post("/api/auth/change-password")
def change_password(
    password_data: dict,
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        # Get current user from database
        user_result = (
            db.table("users")
            .select("*")
            .eq("id", current_user["id"])
            .execute()
        )
        
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = user_result.data[0]
        
        # Verify old password
        if not auth.verify_password(password_data.get("old_password"), user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_password_hash = auth.hash_password(password_data.get("new_password"))
        
        # Update password
        update_result = (
            db.table("users")
            .update({"password_hash": new_password_hash})
            .eq("id", current_user["id"])
            .execute()
        )
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return {"message": "Password changed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )

# ============================================
# INSIGHTS: GET
# ============================================
@app.get("/api/insights")
def get_insights(
    current_user=Depends(auth.get_current_user),
    db=Depends(get_db),
):
    try:
        # Get transactions
        transactions_result = (
            db.table("transactions")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        transactions = transactions_result.data if transactions_result.data else []
        
        # Calculate current month and last month totals
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        current_month_total = sum(
            t["amount"] for t in transactions 
            if t["transaction_type"] == "expense" and 
            datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).month == current_month and
            datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).year == current_year
        )
        
        last_month = current_month - 1 if current_month > 1 else 12
        last_month_year = current_year if current_month > 1 else current_year - 1
        
        last_month_total = sum(
            t["amount"] for t in transactions 
            if t["transaction_type"] == "expense" and 
            datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).month == last_month and
            datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).year == last_month_year
        )
        
        difference = current_month_total - last_month_total
        percent_change = ((difference / last_month_total) * 100) if last_month_total > 0 else 0
        
        # Calculate total expenses and category breakdown
        total_expenses = sum(t["amount"] for t in transactions if t["transaction_type"] == "expense")
        
        category_breakdown = {}
        for t in transactions:
            if t["transaction_type"] == "expense":
                category = t["category"]
                category_breakdown[category] = category_breakdown.get(category, 0) + t["amount"]
        
        # Find top spending category
        top_category = max(category_breakdown.items(), key=lambda x: x[1]) if category_breakdown else ("None", 0)
        
        # Generate AI-powered recommendations
        recommendations = []
        
        # Recommendation 1: Spending trend
        if difference > 0:
            recommendations.append({
                "category": "Spending Alert",
                "message": f"Your spending increased by ₹{abs(difference):.2f} ({abs(percent_change):.1f}%) compared to last month. Consider reviewing your expenses.",
                "type": "warning"
            })
        elif difference < 0:
            recommendations.append({
                "category": "Great Progress",
                "message": f"Excellent! You reduced spending by ₹{abs(difference):.2f} ({abs(percent_change):.1f}%) compared to last month.",
                "type": "success"
            })
        else:
            recommendations.append({
                "category": "Stable Spending",
                "message": "Your spending is consistent with last month. Keep maintaining this pattern.",
                "type": "info"
            })
        
        # Recommendation 2: Top spending category
        if top_category[1] > 0:
            category_percentage = (top_category[1] / total_expenses * 100) if total_expenses > 0 else 0
            if category_percentage > 40:
                recommendations.append({
                    "category": "Category Alert",
                    "message": f"{top_category[0]} accounts for {category_percentage:.1f}% of your expenses (₹{top_category[1]:.2f}). Consider setting a budget for this category.",
                    "type": "warning"
                })
            else:
                recommendations.append({
                    "category": "Top Spending",
                    "message": f"Your highest spending is in {top_category[0]} (₹{top_category[1]:.2f}). This is {category_percentage:.1f}% of total expenses.",
                    "type": "info"
                })
        
        # Recommendation 3: Savings opportunity
        if total_expenses > 0:
            potential_savings = total_expenses * 0.1  # Suggest 10% reduction
            recommendations.append({
                "category": "Savings Opportunity",
                "message": f"By reducing expenses by just 10%, you could save ₹{potential_savings:.2f} per month, which is ₹{potential_savings * 12:.2f} annually!",
                "type": "success"
            })
        
        # Recommendation 4: Transaction frequency
        transaction_count = len([t for t in transactions if t["transaction_type"] == "expense"])
        if transaction_count > 50:
            recommendations.append({
                "category": "Transaction Pattern",
                "message": f"You have {transaction_count} expense transactions. Consider consolidating purchases to reduce impulse spending.",
                "type": "info"
            })
        
        # Recommendation 5: Budget allocation check
        try:
            budget_result = (
                db.table("budget_plans")
                .select("*")
                .eq("user_id", current_user["id"])
                .eq("month", datetime.utcnow().strftime("%Y-%m"))
                .execute()
            )
            
            if budget_result.data:
                # Calculate current month expenses by category
                current_month_expenses = {}
                for t in transactions:
                    if t["transaction_type"] == "expense":
                        try:
                            date = datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00"))
                            if date.month == current_month and date.year == current_year:
                                category = t["category"]
                                current_month_expenses[category] = current_month_expenses.get(category, 0) + t["amount"]
                        except:
                            continue
                
                # Check for budget overruns
                budget_allocations = {}
                for budget in budget_result.data:
                    budget_allocations[budget["category"]] = budget["allocated_amount"]
                
                overrun_count = 0
                anomaly_records = []
                for category, spent in current_month_expenses.items():
                    if category in budget_allocations:
                        allocated = budget_allocations[category]
                        if spent > allocated:
                            overrun_amount = spent - allocated
                            overrun_percent = (overrun_amount / allocated * 100) if allocated > 0 else 0
                            
                            # Add to recommendations
                            recommendations.append({
                                "category": f"{category} Budget Alert",
                                "message": f"You've exceeded your {category} budget by ₹{overrun_amount:.2f} ({overrun_percent:.1f}%). Allocated: ₹{allocated:.2f}, Spent: ₹{spent:.2f}",
                                "type": "warning"
                            })
                            
                            # Prepare anomaly record
                            anomaly_records.append({
                                "user_id": current_user["id"],
                                "category": category,
                                "description": f"Budget exceeded by ₹{overrun_amount:.2f} ({overrun_percent:.1f}%)",
                                "detected_at": datetime.utcnow().isoformat()
                            })
                            overrun_count += 1
                
                # Insert all anomaly records at once
                if anomaly_records:
                    try:
                        db.table("anomalies").insert(anomaly_records).execute()
                    except Exception as e:
                        print(f"Failed to insert anomalies: {str(e)}")
                
                if overrun_count > 0:
                    recommendations.append({
                        "category": "Budget Management",
                        "message": f"You have {overrun_count} categories exceeding their allocated budgets. Review your spending to stay on track.",
                        "type": "warning"
                    })
        except Exception as e:
            print(f"Error in budget allocation check: {str(e)}")
        
        # Ensure minimum 5 recommendations
        while len(recommendations) < 5:
            if len(recommendations) == 4:
                recommendations.append({
                    "category": "Financial Health",
                    "message": "Track your expenses regularly to identify spending patterns and opportunities for savings.",
                    "type": "info"
                })
            elif len(recommendations) == 3:
                recommendations.append({
                    "category": "Smart Budgeting",
                    "message": "Set monthly budgets for each spending category to maintain better control over your finances.",
                    "type": "info"
                })
            elif len(recommendations) == 2:
                recommendations.append({
                    "category": "Emergency Fund",
                    "message": "Build an emergency fund covering 3-6 months of expenses for financial security.",
                    "type": "success"
                })
            elif len(recommendations) == 1:
                recommendations.append({
                    "category": "Investment Planning",
                    "message": "Consider investing your savings in diversified portfolios for long-term wealth creation.",
                    "type": "success"
                })
            else:
                recommendations.append({
                    "category": "Getting Started",
                    "message": "Start by adding your income and setting expense limits to get personalized insights.",
                    "type": "info"
                })
        
        # Generate summary
        if total_expenses == 0:
            summary = "Start tracking your expenses to get personalized insights and recommendations. Add your first transaction to begin your financial journey!"
        else:
            summary = f"Based on your spending patterns, you've spent ₹{total_expenses:.2f} across {len(category_breakdown)} categories. "
            if difference > 0:
                summary += f"Your spending increased by {abs(percent_change):.1f}% this month. "
            elif difference < 0:
                summary += f"Great job! You reduced spending by {abs(percent_change):.1f}% this month. "
            summary += f"Focus on optimizing your {top_category[0]} expenses for maximum savings impact."
        
        # Get anomalies
        anomalies_result = (
            db.table("anomalies")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        
        anomalies = anomalies_result.data if anomalies_result.data else []
        
        insights = {
            "summary": summary,
            "recommendations": recommendations,
            "anomalies": anomalies,
            "current_month_total": current_month_total,
            "last_month_total": last_month_total,
            "difference": difference,
            "percent_change": percent_change,
            "total_expenses": total_expenses,
            "category_breakdown": category_breakdown,
            "top_spending_category": top_category[0],
            "top_spending_amount": top_category[1],
            "transaction_count": transaction_count
        }
        
        return insights
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch insights: {str(e)}"
        )
