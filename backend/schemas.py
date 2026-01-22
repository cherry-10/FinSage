from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

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
    email: str
    phone: str
    profile_photo: Optional[str] = None
    annual_salary: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    annual_salary: Optional[float] = None
    profile_photo: Optional[str] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class IncomeCreate(BaseModel):
    monthly_income: float

class IncomeResponse(BaseModel):
    id: int
    user_id: int
    monthly_income: float
    created_at: datetime

    class Config:
        from_attributes = True

class ExpenseLimitCreate(BaseModel):
    monthly_limit: float
    target_savings: float

class ExpenseLimitResponse(BaseModel):
    id: int
    user_id: int
    monthly_limit: float
    target_savings: float
    created_at: datetime

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

class BudgetPlanResponse(BaseModel):
    id: int
    user_id: int
    month: str
    category: str
    allocated_amount: float
    created_at: datetime

    class Config:
        from_attributes = True

class AnomalyResponse(BaseModel):
    id: int
    user_id: int
    category: str
    issue: str
    impact_amount: float
    recommendation: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserSettingsUpdate(BaseModel):
    notifications_enabled: Optional[int] = None
    dark_mode: Optional[int] = None
    anomaly_alerts: Optional[int] = None

class UserSettingsResponse(BaseModel):
    id: int
    user_id: int
    notifications_enabled: int
    dark_mode: int
    anomaly_alerts: int

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_income: float
    total_expenses: float
    savings: float
    anomaly_count: int
    last_month_expenses: float
    this_month_expenses: float
    recent_transactions: List[TransactionResponse]
