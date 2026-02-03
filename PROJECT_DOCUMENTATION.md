# FinSage - Personal Finance Management System

## 📋 Project Overview

**FinSage** is a full-stack personal finance management application that helps users track expenses, manage budgets, detect spending anomalies, and receive AI-powered financial insights. The application uses modern web technologies with a React frontend and FastAPI backend, deployed on Vercel and Render respectively.

---

## 🏗️ Architecture

### **Tech Stack**

**Frontend:**
- React 18 with Vite
- Tailwind CSS for styling
- Recharts for data visualization
- Lucide React for icons
- Axios for API calls
- React Router for navigation
- Date-fns for date handling

**Backend:**
- FastAPI (Python web framework)
- Supabase (PostgreSQL database)
- Groq AI (LLaMA 3 for insights)
- Bcrypt for password hashing
- JWT for authentication
- Python-Jose for token management

**Deployment:**
- Frontend: Vercel
- Backend: Render (Free tier)
- Database: Supabase (PostgreSQL)

---

## 📁 Project Structure

```
finsage/
├── backend/
│   ├── main.py              # Main FastAPI application with all endpoints
│   ├── auth.py              # Authentication utilities (JWT, bcrypt)
│   ├── database.py          # Supabase client configuration
│   ├── config.py            # Environment configuration
│   ├── schemas.py           # Pydantic models for request/response
│   ├── ai_service.py        # AI-powered budget and anomaly detection
│   ├── requirements.txt     # Python dependencies
│   └── render.yaml          # Render deployment configuration
│
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   │   ├── Navbar.jsx
│   │   │   ├── Footer.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── context/         # React context providers
│   │   │   ├── AuthContext.jsx
│   │   │   └── ThemeContext.jsx
│   │   ├── pages/           # Main application pages
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Transactions.jsx
│   │   │   ├── Budget.jsx
│   │   │   ├── Insights.jsx
│   │   │   ├── Profile.jsx
│   │   │   ├── Login.jsx
│   │   │   └── Register.jsx
│   │   ├── services/        # API service layer
│   │   │   └── api.js
│   │   ├── App.jsx          # Main app component with routing
│   │   └── main.jsx         # Application entry point
│   ├── public/
│   │   └── _redirects       # SPA routing for Vercel
│   ├── vercel.json          # Vercel deployment configuration
│   └── package.json         # Frontend dependencies
│
└── README.md                # Project documentation
```

---

## 🔧 Backend Components

### **1. main.py - Core API Endpoints**

The main FastAPI application file containing all REST API endpoints.

#### **Authentication Endpoints**
- `POST /api/auth/register` - User registration with password hashing
- `POST /api/auth/login` - User login with JWT token generation
- `GET /api/auth/me` - Get current authenticated user

#### **Dashboard Endpoints**
- `GET /api/dashboard/stats?period={current_month|last_month|all_time}` - Get financial statistics
  - Calculates income, expenses, savings
  - Supports three time periods with different calculation logic
  - All Time: `income = (monthly_salary × months_with_data) + positive_transactions`
  - Detects budget overruns for anomaly count
  
- `GET /api/dashboard/trends?period={current_month|last_month|all_time}` - Get spending trends
  - Daily expense trends for current/last month
  - Category breakdown
  - Monthly expenses for all-time view

#### **Transaction Endpoints**
- `GET /api/transactions` - Get all user transactions
- `POST /api/transactions` - Create new transaction
- `PUT /api/transactions/{id}` - Update transaction
- `DELETE /api/transactions/{id}` - Delete transaction

#### **Budget Endpoints**
- `POST /api/budget/generate` - Generate AI-powered budget plan
  - Uses annual salary or income table
  - Calculates target savings (20% of income by default)
  - Allocates budget across 9 categories based on priority
  - Considers past spending patterns
  
- `GET /api/budget` - Get current month's budget plan
- `GET /api/budget/summary` - Get budget vs actual spending comparison

#### **Anomaly Detection Endpoints**
- `POST /api/anomalies/detect` - Detect spending anomalies using AI
- `GET /api/anomalies` - Get detected anomalies

#### **Insights Endpoints**
- `GET /api/insights` - Get AI-powered financial insights
  - Compares current vs last month spending
  - Identifies top spending categories
  - Calculates savings opportunities
  - Detects budget overruns automatically
  - Generates minimum 5 quality recommendations
  - Creates anomaly records when budgets exceeded

#### **Profile Endpoints**
- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update user profile (name, annual salary)

---

### **2. auth.py - Authentication System**

Handles user authentication and authorization.

**Key Features:**
- **Password Hashing**: Bcrypt with 10 rounds (optimized for performance)
- **JWT Tokens**: HS256 algorithm with configurable expiration
- **Token Validation**: Middleware for protected routes
- **User Verification**: Validates credentials against Supabase users table

**Functions:**
- `verify_password(plain, hashed)` - Compare passwords
- `hash_password(password)` - Hash new passwords
- `create_access_token(data)` - Generate JWT tokens
- `get_current_user(token)` - Validate and extract user from token

---

### **3. database.py - Database Client**

Manages Supabase PostgreSQL database connection.

**Key Features:**
- **Singleton Pattern**: Single cached client instance using `@lru_cache`
- **HTTP-based**: Uses Supabase Python client (no direct PostgreSQL connection)
- **Service Role Key**: Backend uses privileged access for all operations
- **Health Check**: Validates database connectivity

**Database Tables:**
- `users` - User accounts (id, email, password_hash, name, annual_salary)
- `transactions` - Financial transactions (user_id, amount, category, type, date)
- `budget_plans` - Monthly budget allocations (user_id, month, category, allocated_amount)
- `anomalies` - Detected spending anomalies (user_id, category, description, detected_at)
- `income` - Income records (user_id, monthly_income)
- `expense_limits` - Monthly spending limits (user_id, monthly_limit)

---

### **4. ai_service.py - AI-Powered Features**

Implements intelligent budget generation and anomaly detection using Groq AI (LLaMA 3).

#### **Budget Generation Algorithm**

**Function:** `generate_budget_plan(income, target_savings, past_expenses, loan_commitments)`

**Logic:**
1. Calculate spendable amount: `income - target_savings - loans`
2. Allocate across 9 categories with priority-based percentages:
   - **Priority 1** (Essential): Rent (25-35%), Food (15-25%), Bills (10-15%), Healthcare (5-10%)
   - **Priority 2** (Important): Transport (8-12%), Education (5-15%)
   - **Priority 3** (Discretionary): Shopping (5-10%), Entertainment (3-8%), Other (2-5%)
3. Adjust allocations based on past spending patterns
4. Ensure total never exceeds spendable amount
5. Apply proportional reduction if needed

**Example:**
```
Income: ₹50,000
Target Savings: ₹10,000
Spendable: ₹40,000

Budget Allocation:
- Rent: ₹12,000 (30%)
- Food: ₹8,000 (20%)
- Bills: ₹5,000 (12.5%)
- Transport: ₹4,000 (10%)
- Healthcare: ₹3,000 (7.5%)
- Education: ₹3,000 (7.5%)
- Shopping: ₹2,500 (6.25%)
- Entertainment: ₹2,000 (5%)
- Other: ₹500 (1.25%)
Total: ₹40,000 ✅
```

#### **Anomaly Detection**

**Function:** `detect_anomalies(income, monthly_limit, target_savings, current_expenses, budget_allocations, last_month_expenses)`

**Detection Rules:**
1. **Category Overspending**: Current > allocated budget
2. **Expense Spike**: >30% increase vs last month
3. **Large Transactions**: Single expense >2× average
4. **Budget Risk**: Total expenses >90% of monthly limit
5. **Budget Exceeded**: Total expenses > monthly limit

**Fallback System:**
- Primary: Groq AI (LLaMA 3) for intelligent analysis
- Fallback: Rule-based detection if API fails
- Always returns actionable recommendations

---

### **5. config.py - Configuration Management**

Manages environment variables and application settings.

**Environment Variables:**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Backend service role key
- `SECRET_KEY` - JWT signing secret
- `GROQ_API_KEY` - Groq AI API key
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT expiration time

---

### **6. schemas.py - Data Models**

Pydantic models for request/response validation.

**Key Schemas:**
- `UserCreate`, `UserResponse` - User registration/profile
- `Token` - JWT authentication response
- `TransactionCreate`, `TransactionResponse` - Transaction operations
- `BudgetPlanResponse` - Budget allocation data
- `ProfileUpdate` - User profile updates

---

## 🎨 Frontend Components

### **Pages**

#### **1. Dashboard.jsx**
Main overview page showing financial summary.

**Features:**
- **Filter Tabs**: Current Month, Last Month, All Time
- **Stats Cards**: Income, Expenses, Savings, Alerts (anomaly count)
- **Graphs**: 
  - Current/Last Month: Daily expense trends, category breakdown
  - All Time: Monthly expenses bar chart
- **Recent Transactions**: Last 5 transactions
- **Category Breakdown**: Pie chart visualization

**Key Logic:**
- Fetches data based on selected period
- Handles blank cards with default values
- Error handling for API failures
- Real-time anomaly count updates

#### **2. Transactions.jsx**
Transaction management page.

**Features:**
- Add new transactions (expense/income)
- Edit existing transactions
- Delete transactions
- Filter by category and type
- Search functionality
- Pagination

**Categories:**
- Food, Transport, Shopping, Bills, Entertainment, Healthcare, Education, Rent, Other

#### **3. Budget.jsx**
Budget planning and tracking page.

**Features:**
- Generate AI-powered budget
- View current month's budget allocations
- Compare allocated vs actual spending
- Visual progress bars for each category
- Budget utilization percentage

**Budget Generation:**
- Uses annual salary from profile
- Calculates 80% for expenses, 20% for savings
- Considers past spending patterns
- Generates 9-category budget plan

#### **4. Insights.jsx**
AI-powered financial insights and recommendations.

**Features:**
- AI analysis summary
- Spending comparison (current vs last month)
- Minimum 5 quality recommendations
- Detected anomalies list
- Actionable financial advice

**Recommendation Types:**
- Spending trend alerts
- Category-specific insights
- Savings opportunities
- Budget overrun warnings
- Financial health tips
- Emergency fund guidance
- Investment suggestions

#### **5. Profile.jsx**
User profile management.

**Features:**
- Update name
- Set annual salary
- View account information
- Logout functionality

#### **6. Login.jsx & Register.jsx**
Authentication pages.

**Features:**
- Email/password authentication
- Form validation
- Error handling
- Redirect after successful auth

---

### **Components**

#### **1. Navbar.jsx**
Navigation bar with theme toggle.

**Features:**
- Logo and branding
- Navigation links (Dashboard, Transactions, Budget, Insights, Profile)
- Dark/light theme toggle
- Responsive mobile menu

#### **2. Footer.jsx**
Application footer.

**Features:**
- Copyright information
- Social media links (GitHub, LinkedIn, Email)
- Opens links in new tabs

#### **3. ProtectedRoute.jsx**
Route protection wrapper.

**Features:**
- Checks authentication status
- Redirects to login if not authenticated
- Shows loading state during auth check

---

### **Context Providers**

#### **1. AuthContext.jsx**
Global authentication state management.

**Features:**
- User state management
- Login/logout functions
- Token storage in localStorage
- Auto-fetch user on mount
- Register functionality

#### **2. ThemeContext.jsx**
Dark/light theme management.

**Features:**
- Theme state (dark/light)
- Toggle function
- Persists preference in localStorage
- Applies theme class to document

---

### **Services**

#### **api.js**
Centralized API service layer.

**Features:**
- Axios instance with base URL
- Automatic token injection
- Request/response interceptors
- Organized API methods by feature:
  - `authAPI` - Authentication
  - `dashboardAPI` - Dashboard data
  - `transactionsAPI` - Transaction CRUD
  - `budgetAPI` - Budget operations
  - `insightsAPI` - AI insights
  - `profileAPI` - Profile management

---

## 🔄 Data Flow

### **Authentication Flow**
1. User submits login form
2. Frontend sends credentials to `/api/auth/login`
3. Backend validates against Supabase users table
4. Backend generates JWT token
5. Frontend stores token in localStorage
6. Token included in all subsequent requests via Authorization header

### **Dashboard Data Flow**
1. User selects period filter (Current Month, Last Month, All Time)
2. Frontend calls `/api/dashboard/stats?period={period}`
3. Backend queries transactions from Supabase
4. Backend calculates income, expenses, savings based on period
5. Backend checks for budget overruns (anomaly count)
6. Frontend displays stats cards and graphs
7. Parallel call to `/api/dashboard/trends` for graph data

### **Budget Generation Flow**
1. User clicks "Generate AI Budget"
2. Frontend calls `/api/budget/generate`
3. Backend fetches user's annual salary
4. Backend calculates target savings (20% of income)
5. Backend retrieves past transactions for pattern analysis
6. AI service allocates budget across 9 categories
7. Backend stores budget plan in database
8. Frontend displays budget allocations

### **Anomaly Detection Flow**
1. AI Insights page loads
2. Frontend calls `/api/insights`
3. Backend compares current month expenses vs budget allocations
4. For each category where spent > allocated:
   - Creates anomaly record in database
   - Adds budget alert recommendation
5. Backend generates minimum 5 recommendations
6. Dashboard anomaly count updates automatically

---

## 🚀 Deployment

### **Backend (Render)**

**Configuration:** `render.yaml`
```yaml
services:
  - type: web
    name: finsage-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
- SUPABASE_URL
- SUPABASE_SERVICE_KEY
- SECRET_KEY
- GROQ_API_KEY

**URL:** `https://finsage-xabw.onrender.com`

### **Frontend (Vercel)**

**Configuration:** `vercel.json`
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

**SPA Routing:** `public/_redirects`
```
/*    /index.html   200
```

**URL:** `https://fin-sage-nks6.vercel.app`

---

## 🔑 Key Features

### **1. Multi-Period Dashboard**
- Current Month: Shows this month's income, expenses, savings
- Last Month: Historical comparison
- All Time: Lifetime financial overview with accurate income calculation

### **2. Smart Income Calculation**
- All Time income = (monthly_salary × months_with_data) + positive_transactions
- Prevents negative savings
- Accurate multi-month tracking

### **3. AI-Powered Budget Generation**
- Priority-based allocation (Essential → Important → Discretionary)
- Past spending pattern analysis
- Automatic adjustment to prevent overspending
- 9-category budget plan

### **4. Real-Time Anomaly Detection**
- Automatic detection when budgets exceeded
- Dashboard anomaly count updates immediately
- Detailed recommendations with specific amounts
- Tracks overspend percentage

### **5. Quality Financial Insights**
- Minimum 5 recommendations guaranteed
- Spending trend analysis
- Category-specific advice
- Savings opportunities
- Emergency fund guidance
- Investment suggestions

### **6. Dark/Light Theme**
- User preference persistence
- Smooth theme transitions
- Consistent styling across all pages

### **7. Responsive Design**
- Mobile-friendly layout
- Touch-optimized interactions
- Adaptive navigation

---

## 🛡️ Security

### **Authentication**
- Bcrypt password hashing (10 rounds)
- JWT tokens with expiration
- Protected API routes
- Token validation middleware

### **Authorization**
- User-specific data isolation
- All queries filtered by user_id
- Service role key for backend only
- No direct database access from frontend

### **Data Validation**
- Pydantic schemas for request validation
- Type checking on all inputs
- SQL injection prevention via Supabase client
- XSS protection in React

---

## 📊 Database Schema

### **users**
```sql
id: UUID (primary key)
email: VARCHAR (unique)
password_hash: VARCHAR
name: VARCHAR
annual_salary: NUMERIC
created_at: TIMESTAMP
```

### **transactions**
```sql
id: UUID (primary key)
user_id: UUID (foreign key)
amount: NUMERIC
category: VARCHAR
transaction_type: VARCHAR (expense/income)
transaction_date: TIMESTAMP
description: TEXT
created_at: TIMESTAMP
```

### **budget_plans**
```sql
id: UUID (primary key)
user_id: UUID (foreign key)
month: VARCHAR (YYYY-MM)
category: VARCHAR
allocated_amount: NUMERIC
created_at: TIMESTAMP
```

### **anomalies**
```sql
id: UUID (primary key)
user_id: UUID (foreign key)
category: VARCHAR
description: TEXT
detected_at: TIMESTAMP
```

---

## 🐛 Bug Fixes & Improvements

### **Fixed Issues**
1. ✅ 404 error on page refresh (SPA routing)
2. ✅ Negative savings in All Time filter (income calculation)
3. ✅ 500 error on Last Month filter (date parsing)
4. ✅ Blank dashboard cards (error handling)
5. ✅ Budget generation 400 error (parameter mismatch)
6. ✅ Budget generation 500 error (function signature)
7. ✅ AI Insights 500 error (anomaly detection crash)
8. ✅ Dashboard anomaly count always 0 (real-time calculation)

### **Performance Optimizations**
1. Bcrypt rounds reduced to 10 (faster login)
2. Batch database inserts (anomaly records)
3. Cached Supabase client (singleton pattern)
4. Error handling prevents cascading failures

---

## 📝 API Response Examples

### **Dashboard Stats**
```json
{
  "total_income": 50000,
  "total_expenses": 22149,
  "savings": 27851,
  "anomaly_count": 2,
  "recent_transactions": [...],
  "category_breakdown": [
    {"category": "Food", "total": 10500},
    {"category": "Transport", "total": 4000}
  ]
}
```

### **AI Insights**
```json
{
  "summary": "Based on your spending patterns, you've spent ₹22,149 across 8 categories...",
  "recommendations": [
    {
      "category": "Food Budget Alert",
      "message": "You've exceeded your Food budget by ₹2,500 (31.3%)...",
      "type": "warning"
    }
  ],
  "anomalies": [
    {
      "category": "Food",
      "description": "Budget exceeded by ₹2,500 (31.3%)",
      "detected_at": "2026-02-04T01:11:00"
    }
  ],
  "current_month_total": 22149,
  "last_month_total": 20149,
  "difference": 2000,
  "percent_change": 9.9
}
```

---

## 🚦 Getting Started

### **Prerequisites**
- Node.js 18+
- Python 3.9+
- Supabase account
- Groq API key

### **Backend Setup**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

### **Environment Variables**

**Backend (.env):**
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
SECRET_KEY=your_jwt_secret
GROQ_API_KEY=your_groq_key
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

**Frontend (.env):**
```
VITE_API_URL=http://localhost:8000
```

---

## 📞 Contact

- **GitHub:** [cherry-10](https://github.com/cherry-10/)
- **LinkedIn:** [charan-teja-995a0a31a](https://www.linkedin.com/in/charan-teja-995a0a31a/)
- **Email:** charanteja1039@gmail.com

---

## 📄 License

This project is open source and available for educational purposes.

---

**Last Updated:** February 4, 2026
**Version:** 1.0.0
**Status:** Production Ready ✅
