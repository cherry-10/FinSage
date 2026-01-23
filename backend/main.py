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
            .select("id, name, email, phone, profile_photo, created_at")
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
        
        # Get latest expense limit
        limit_result = (
            db.table("expense_limits")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        if not income_result.data or not limit_result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please set your income and expense limits first"
            )
        
        income = income_result.data[0]["monthly_income"]
        expense_limit = limit_result.data[0]["monthly_limit"]
        
        # Get user transactions for AI analysis
        transactions_result = (
            db.table("transactions")
            .select("*")
            .eq("user_id", current_user["id"])
            .limit(50)
            .execute()
        )
        
        # Generate budget using AI
        budget_plan = generate_budget_plan(
            income=income,
            expense_limit=expense_limit,
            transactions=transactions_result.data
        )
        
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
        # Get all transactions
        transactions_result = (
            db.table("transactions")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        transactions = transactions_result.data if transactions_result.data else []
        
        # Calculate stats
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        total_income = sum(t["amount"] for t in transactions if t["transaction_type"] == "income")
        total_expenses = sum(t["amount"] for t in transactions if t["transaction_type"] == "expense")
        
        this_month_expenses = sum(
            t["amount"] for t in transactions 
            if t["transaction_type"] == "expense" and 
            datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).month == current_month and
            datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).year == current_year
        )
        
        last_month = current_month - 1 if current_month > 1 else 12
        last_month_year = current_year if current_month > 1 else current_year - 1
        
        last_month_expenses = sum(
            t["amount"] for t in transactions 
            if t["transaction_type"] == "expense" and 
            datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).month == last_month and
            datetime.fromisoformat(t["transaction_date"].replace("Z", "+00:00")).year == last_month_year
        )
        
        # Get anomaly count
        anomalies_result = (
            db.table("anomalies")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        anomaly_count = len(anomalies_result.data) if anomalies_result.data else 0
        
        # Get recent transactions
        recent_transactions = sorted(
            transactions,
            key=lambda x: x["transaction_date"],
            reverse=True
        )[:5]
        
        # Calculate category breakdown
        category_totals = {}
        for t in transactions:
            if t["transaction_type"] == "expense":
                category = t["category"]
                category_totals[category] = category_totals.get(category, 0) + t["amount"]
        
        category_breakdown = [
            {"category": cat, "total": total}
            for cat, total in category_totals.items()
        ]
        
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "savings": total_income - total_expenses,
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
        # Get transactions
        transactions_result = (
            db.table("transactions")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        transactions = transactions_result.data if transactions_result.data else []
        
        # Calculate trends by category
        category_totals = {}
        for t in transactions:
            if t["transaction_type"] == "expense":
                category = t["category"]
                category_totals[category] = category_totals.get(category, 0) + t["amount"]
        
        return {"trends": category_totals}
    
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
        if "annual_income" in user_data:
            update_data["annual_income"] = user_data["annual_income"]
        
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
