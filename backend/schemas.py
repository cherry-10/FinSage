from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# ============================================
# AUTH SCHEMAS
# ============================================
class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    profile_photo: Optional[str] = None
    annual_salary: Optional[float] = None
    created_at: Optional[str] = None


# ============================================
# TRANSACTION SCHEMAS
# ============================================
class TransactionCreate(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None
    transaction_type: str = "expense"
    transaction_date: Optional[datetime] = None


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    category: str
    description: Optional[str]
    transaction_type: str
    transaction_date: datetime


# ============================================
# INCOME SCHEMAS
# ============================================
class IncomeCreate(BaseModel):
    monthly_income: float


class IncomeResponse(BaseModel):
    id: int
    user_id: int
    monthly_income: float
    created_at: datetime


# ============================================
# EXPENSE LIMIT SCHEMAS
# ============================================
class ExpenseLimitCreate(BaseModel):
    monthly_limit: float
    target_savings: float


class ExpenseLimitResponse(BaseModel):
    id: int
    user_id: int
    monthly_limit: float
    target_savings: float
    created_at: datetime


# ============================================
# BUDGET SCHEMAS
# ============================================
class BudgetPlanResponse(BaseModel):
    id: int
    user_id: int
    month: str
    category: str
    allocated_amount: float
    created_at: datetime


# ============================================
# ANOMALY SCHEMAS
# ============================================
class AnomalyResponse(BaseModel):
    id: int
    user_id: int
    category: str
    issue: str
    impact_amount: float
    recommendation: str
    created_at: datetime


# ============================================
# USER SETTINGS
# ============================================
class UserSettingsUpdate(BaseModel):
    notifications_enabled: Optional[bool] = None
    dark_mode: Optional[bool] = None
    anomaly_alerts: Optional[bool] = None


class UserSettingsResponse(BaseModel):
    id: int
    user_id: int
    notifications_enabled: bool
    dark_mode: bool
    anomaly_alerts: bool


# ============================================
# DASHBOARD SCHEMAS
# ============================================
class DashboardStats(BaseModel):
    total_income: float
    total_expenses: float
    savings: float
    anomaly_count: int
    last_month_expenses: float
    this_month_expenses: float
    recent_transactions: List[TransactionResponse]
