from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import List
import models
import schemas
import auth
from database import get_db, init_db
from ai_service import generate_budget_plan, detect_anomalies, get_financial_recommendations
import base64
import os

app = FastAPI(title="FinSage API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://finsage.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {"message": "FinSage API is running", "status": "healthy"}

@app.post("/api/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    user_settings = models.UserSettings(user_id=db_user.id)
    db.add(user_settings)
    db.commit()
    
    return db_user

@app.post("/api/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: models.User = Depends(auth.get_current_user)):
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    return current_user

@app.put("/api/auth/me", response_model=schemas.UserResponse)
def update_user(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if user_update.name is not None:
        current_user.name = user_update.name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.annual_salary is not None:
        current_user.annual_salary = user_update.annual_salary
    if user_update.profile_photo is not None:
        current_user.profile_photo = user_update.profile_photo
    
    db.commit()
    db.refresh(current_user)
    return current_user

@app.post("/api/auth/change-password")
def change_password(
    password_change: schemas.PasswordChange,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not auth.verify_password(password_change.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    current_user.password_hash = auth.get_password_hash(password_change.new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@app.post("/api/income", response_model=schemas.IncomeResponse)
def create_income(
    income: schemas.IncomeCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_income = models.Income(user_id=current_user.id, monthly_income=income.monthly_income)
    db.add(db_income)
    db.commit()
    db.refresh(db_income)
    return db_income

@app.get("/api/income/latest", response_model=schemas.IncomeResponse)
def get_latest_income(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    income = db.query(models.Income).filter(
        models.Income.user_id == current_user.id
    ).order_by(models.Income.created_at.desc()).first()
    
    if not income:
        raise HTTPException(status_code=404, detail="No income data found")
    return income

@app.post("/api/expense-limits", response_model=schemas.ExpenseLimitResponse)
def create_expense_limit(
    expense_limit: schemas.ExpenseLimitCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_limit = models.ExpenseLimit(
        user_id=current_user.id,
        monthly_limit=expense_limit.monthly_limit,
        target_savings=expense_limit.target_savings
    )
    db.add(db_limit)
    db.commit()
    db.refresh(db_limit)
    return db_limit

@app.get("/api/expense-limits/latest", response_model=schemas.ExpenseLimitResponse)
def get_latest_expense_limit(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    limit = db.query(models.ExpenseLimit).filter(
        models.ExpenseLimit.user_id == current_user.id
    ).order_by(models.ExpenseLimit.created_at.desc()).first()
    
    if not limit:
        raise HTTPException(status_code=404, detail="No expense limit data found")
    return limit

@app.post("/api/transactions", response_model=schemas.TransactionResponse)
def create_transaction(
    transaction: schemas.TransactionCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_transaction = models.Transaction(
        user_id=current_user.id,
        amount=abs(transaction.amount),
        category=transaction.category,
        description=transaction.description,
        transaction_type=transaction.transaction_type,
        transaction_date=transaction.transaction_date or datetime.utcnow()
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction

@app.get("/api/transactions", response_model=List[schemas.TransactionResponse])
def get_transactions(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    ).order_by(models.Transaction.transaction_date.desc()).all()
    return transactions

@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}

@app.post("/api/budget/generate")
def generate_budget(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    expense_limit = db.query(models.ExpenseLimit).filter(
        models.ExpenseLimit.user_id == current_user.id
    ).order_by(models.ExpenseLimit.created_at.desc()).first()
    
    if not expense_limit:
        raise HTTPException(status_code=400, detail="Please set expense limits first")
    
    # CRITICAL: Use monthly income from annual_salary / 12
    if not current_user.annual_salary:
        raise HTTPException(status_code=400, detail="Please set your annual salary in profile first")
    
    monthly_income = current_user.annual_salary / 12
    
    budget_data = generate_budget_plan(monthly_income, expense_limit.target_savings)
    
    current_month = datetime.utcnow().strftime("%Y-%m")
    
    db.query(models.BudgetPlan).filter(
        models.BudgetPlan.user_id == current_user.id,
        models.BudgetPlan.month == current_month
    ).delete()
    
    for item in budget_data:
        db_budget = models.BudgetPlan(
            user_id=current_user.id,
            month=current_month,
            category=item["category"],
            allocated_amount=item["allocated_amount"]
        )
        db.add(db_budget)
    
    db.commit()
    
    return {"message": "Budget generated successfully", "budget": budget_data}

@app.get("/api/budget", response_model=List[schemas.BudgetPlanResponse])
def get_budget(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    current_month = datetime.utcnow().strftime("%Y-%m")
    budgets = db.query(models.BudgetPlan).filter(
        models.BudgetPlan.user_id == current_user.id,
        models.BudgetPlan.month == current_month
    ).all()
    return budgets

@app.post("/api/anomalies/detect")
def detect_and_store_anomalies(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    expense_limit = db.query(models.ExpenseLimit).filter(
        models.ExpenseLimit.user_id == current_user.id
    ).order_by(models.ExpenseLimit.created_at.desc()).first()
    
    if not expense_limit:
        raise HTTPException(status_code=400, detail="Please set expense limits first")
    
    # CRITICAL: Use monthly income from annual_salary / 12
    if not current_user.annual_salary:
        raise HTTPException(status_code=400, detail="Please set your annual salary in profile first")
    
    monthly_income = current_user.annual_salary / 12
    
    current_month = datetime.utcnow().replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    current_month_transactions = db.query(
        models.Transaction.category,
        func.sum(models.Transaction.amount).label("total")
    ).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.transaction_type == "expense",
        models.Transaction.transaction_date >= current_month
    ).group_by(models.Transaction.category).all()
    
    last_month_transactions = db.query(
        models.Transaction.category,
        func.sum(models.Transaction.amount).label("total")
    ).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.transaction_type == "expense",
        models.Transaction.transaction_date >= last_month,
        models.Transaction.transaction_date < current_month
    ).group_by(models.Transaction.category).all()
    
    current_expenses = {t.category: float(t.total) for t in current_month_transactions}
    last_month_expenses = {t.category: float(t.total) for t in last_month_transactions}
    
    current_month_str = datetime.utcnow().strftime("%Y-%m")
    budgets = db.query(models.BudgetPlan).filter(
        models.BudgetPlan.user_id == current_user.id,
        models.BudgetPlan.month == current_month_str
    ).all()
    
    budget_allocations = {b.category: float(b.allocated_amount) for b in budgets}
    
    anomalies = detect_anomalies(
        monthly_income,
        expense_limit.monthly_limit,
        expense_limit.target_savings,
        current_expenses,
        budget_allocations,
        last_month_expenses
    )
    
    db.query(models.Anomaly).filter(
        models.Anomaly.user_id == current_user.id,
        func.date(models.Anomaly.created_at) == datetime.utcnow().date()
    ).delete()
    
    for anomaly in anomalies:
        db_anomaly = models.Anomaly(
            user_id=current_user.id,
            category=anomaly["category"],
            issue=anomaly["issue"],
            impact_amount=anomaly["impact_amount"],
            recommendation=anomaly["recommendation"]
        )
        db.add(db_anomaly)
    
    db.commit()
    
    return {"message": "Anomaly detection completed", "anomalies_found": len(anomalies)}

@app.get("/api/anomalies", response_model=List[schemas.AnomalyResponse])
def get_anomalies(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    anomalies = db.query(models.Anomaly).filter(
        models.Anomaly.user_id == current_user.id
    ).order_by(models.Anomaly.created_at.desc()).all()
    return anomalies

@app.get("/api/dashboard", response_model=schemas.DashboardStats)
def get_dashboard_stats(
    period: str = "current_month",
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        current_month = datetime.utcnow().replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        # Determine date range based on period filter
        if period == "last_month":
            target_month_start = last_month
            target_month_end = current_month - timedelta(days=1)
            comparison_month_start = (last_month - timedelta(days=1)).replace(day=1)
            comparison_month_end = last_month - timedelta(days=1)
        else:  # current_month
            target_month_start = current_month
            target_month_end = datetime.utcnow()
            comparison_month_start = last_month
            comparison_month_end = current_month - timedelta(days=1)
        
        target_month_income = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.transaction_type == "income",
            models.Transaction.transaction_date >= target_month_start,
            models.Transaction.transaction_date <= target_month_end
        ).scalar() or 0
        
        target_month_expenses = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.transaction_type == "expense",
            models.Transaction.transaction_date >= target_month_start,
            models.Transaction.transaction_date <= target_month_end
        ).scalar() or 0
        
        comparison_month_expenses = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.transaction_type == "expense",
            models.Transaction.transaction_date >= comparison_month_start,
            models.Transaction.transaction_date <= comparison_month_end
        ).scalar() or 0
        
        if current_user.annual_salary:
            monthly_salary = current_user.annual_salary / 12
            total_income = target_month_income + monthly_salary
        else:
            total_income = target_month_income
        
        savings = total_income - target_month_expenses
        
        anomaly_count = db.query(func.count(models.Anomaly.id)).filter(
            models.Anomaly.user_id == current_user.id
        ).scalar() or 0
        
        recent_transactions = db.query(models.Transaction).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.transaction_date >= target_month_start,
            models.Transaction.transaction_date <= target_month_end
        ).order_by(models.Transaction.transaction_date.desc()).limit(5).all()
        
        return {
            "total_income": float(total_income),
            "total_expenses": float(target_month_expenses),
            "savings": float(savings),
            "anomaly_count": int(anomaly_count),
            "last_month_expenses": float(comparison_month_expenses),
            "this_month_expenses": float(target_month_expenses),
            "recent_transactions": recent_transactions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard stats: {str(e)}")

@app.get("/api/insights")
def get_insights(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        current_month = datetime.utcnow().replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        current_expenses = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.transaction_type == "expense",
            models.Transaction.transaction_date >= current_month
        ).scalar() or 0
        
        last_expenses = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.transaction_type == "expense",
            models.Transaction.transaction_date >= last_month,
            models.Transaction.transaction_date < current_month
        ).scalar() or 0
        
        current_income = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.transaction_type == "income",
            models.Transaction.transaction_date >= current_month
        ).scalar() or 0
        
        if current_user.annual_salary:
            total_income = current_income + (current_user.annual_salary / 12)
        else:
            total_income = current_income
        
        difference = current_expenses - last_expenses
        percent_change = (difference / last_expenses * 100) if last_expenses > 0 else 0
        savings_rate = ((total_income - current_expenses) / total_income * 100) if total_income > 0 else 0
        
        if current_expenses == 0 and last_expenses == 0:
            summary = "Welcome to FinSage! Start tracking your expenses to get personalized financial insights. Add your first transaction to see how we can help you manage your money better."
        else:
            summary = ""
            if difference > 0:
                summary = f"Your spending increased by ₹{abs(difference):.2f} ({abs(percent_change):.1f}%) compared to last month. "
            elif difference < 0:
                summary = f"Great job! Your spending decreased by ₹{abs(difference):.2f} ({abs(percent_change):.1f}%) compared to last month. "
            else:
                summary = "Your spending this month is similar to last month. "
            
            if savings_rate >= 20:
                summary += f"You're saving {savings_rate:.1f}% of your income, which is excellent!"
            elif savings_rate > 0:
                summary += f"You're saving {savings_rate:.1f}% of your income. Try to reach 20% for better financial health."
            else:
                summary += "You're spending more than your income. Consider reducing expenses."
        
        recommendations = []
        
        if current_expenses == 0 and last_expenses == 0:
            recommendations.append({
                "category": "Getting Started",
                "message": "Start by adding your monthly income and setting expense limits to create a personalized budget.",
                "type": "info"
            })
            recommendations.append({
                "category": "Track Expenses",
                "message": "Record your daily expenses to understand your spending patterns and identify areas for improvement.",
                "type": "info"
            })
            recommendations.append({
                "category": "Set Goals",
                "message": "Define your savings goals and let our AI help you achieve them through smart budgeting.",
                "type": "success"
            })
        else:
            if difference > 100:
                recommendations.append({
                    "category": "Spending Control",
                    "message": f"Your expenses increased by ₹{difference:.2f}. Review your spending categories to identify areas to cut back.",
                    "type": "warning"
                })
            
            if savings_rate < 20 and total_income > 0:
                recommendations.append({
                    "category": "Savings",
                    "message": f"Your savings rate is {savings_rate:.1f}%. Financial experts recommend saving at least 20% of your income.",
                    "type": "warning"
                })
            elif savings_rate >= 20:
                recommendations.append({
                    "category": "Savings",
                    "message": f"Excellent! You're saving {savings_rate:.1f}% of your income. Keep up the good work!",
                    "type": "success"
                })
            
            if len(recommendations) == 0:
                recommendations.append({
                    "category": "Financial Health",
                    "message": "Your spending is stable. Continue monitoring your expenses and look for opportunities to increase savings.",
                    "type": "success"
                })
    
        anomalies = db.query(models.Anomaly).filter(
            models.Anomaly.user_id == current_user.id
        ).order_by(models.Anomaly.created_at.desc()).limit(5).all()
        
        return {
            "summary": summary,
            "recommendations": recommendations,
            "anomalies": [{"category": a.category, "description": a.issue, "detected_at": a.created_at} for a in anomalies],
            "current_month_total": float(current_expenses),
            "last_month_total": float(last_expenses),
            "difference": float(difference),
            "percent_change": float(percent_change),
            "savings_rate": float(savings_rate)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch insights: {str(e)}")

@app.get("/api/dashboard/trends")
def get_dashboard_trends(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        current_month = datetime.utcnow().replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        last_month_end = current_month - timedelta(days=1)
        
        this_month_by_category = db.query(
            models.Transaction.category,
            func.sum(models.Transaction.amount).label("total")
        ).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.transaction_type == "expense",
            models.Transaction.transaction_date >= current_month
        ).group_by(models.Transaction.category).all()
        
        last_month_by_category = db.query(
            models.Transaction.category,
            func.sum(models.Transaction.amount).label("total")
        ).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.transaction_type == "expense",
            models.Transaction.transaction_date >= last_month,
            models.Transaction.transaction_date < current_month
        ).group_by(models.Transaction.category).all()
        
        this_month_by_date = db.query(
            func.date(models.Transaction.transaction_date).label("date"),
            func.sum(models.Transaction.amount).label("total")
        ).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.transaction_type == "expense",
            models.Transaction.transaction_date >= current_month
        ).group_by(func.date(models.Transaction.transaction_date)).all()
        
        last_month_by_date = db.query(
            func.date(models.Transaction.transaction_date).label("date"),
            func.sum(models.Transaction.amount).label("total")
        ).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.transaction_type == "expense",
            models.Transaction.transaction_date >= last_month,
            models.Transaction.transaction_date < current_month
        ).group_by(func.date(models.Transaction.transaction_date)).all()
        
        return {
            "this_month_categories": [{"category": t.category, "total": float(t.total)} for t in this_month_by_category],
            "last_month_categories": [{"category": t.category, "total": float(t.total)} for t in last_month_by_category],
            "this_month_daily": [{"date": str(t.date), "total": float(t.total)} for t in this_month_by_date],
            "last_month_daily": [{"date": str(t.date), "total": float(t.total)} for t in last_month_by_date]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")

@app.get("/api/settings", response_model=schemas.UserSettingsResponse)
def get_settings(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = models.UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings

@app.put("/api/settings", response_model=schemas.UserSettingsResponse)
def update_settings(
    settings_update: schemas.UserSettingsUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = models.UserSettings(user_id=current_user.id)
        db.add(settings)
    
    if settings_update.notifications_enabled is not None:
        settings.notifications_enabled = settings_update.notifications_enabled
    if settings_update.dark_mode is not None:
        settings.dark_mode = settings_update.dark_mode
    if settings_update.anomaly_alerts is not None:
        settings.anomaly_alerts = settings_update.anomaly_alerts
    
    db.commit()
    db.refresh(settings)
    return settings

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
