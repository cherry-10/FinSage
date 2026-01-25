# FinSage - AI-Powered Personal Finance Management System

![FinSage](https://img.shields.io/badge/FinSage-v1.0.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green)
![React](https://img.shields.io/badge/React-18.3.1-blue)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-orange)

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

**FinSage** is an intelligent personal finance management application that helps users track expenses, manage budgets, and gain AI-powered insights into their spending patterns. Built with modern web technologies, it provides real-time financial analytics, anomaly detection, and smart budget recommendations.

### Live Deployment
- **Frontend**: https://fin-sage-nks6.vercel.app
- **Backend**: https://finsage-xabw.onrender.com

---

## ✨ Features

### 1. **User Authentication & Profile Management**
- Secure JWT-based authentication
- User registration and login
- Profile management with annual salary tracking
- Password change functionality

### 2. **Transaction Management**
- Add income and expense transactions
- Categorize transactions (Food, Transport, Shopping, Entertainment, Bills, Rent, Healthcare, Education, etc.)
- Filter transactions by month (This Month, Last Month, All Time)
- Filter by category
- Real-time balance calculations
- Delete transactions

### 3. **Dashboard Analytics**
- **KPI Cards**: Income, Expenses, Savings, Anomaly Alerts
- **4 Interactive Graphs**:
  - This Month Daily Expenses (Line Chart)
  - Last Month Daily Expenses (Line Chart)
  - This Month Category Breakdown (Bar Chart)
  - Last Month Category Breakdown (Bar Chart)
- Month filtering (This Month / Last Month)
- Recent transactions list
- Dark mode support

### 4. **AI-Powered Budget Planning**
- Intelligent budget generation using Groq AI
- Category-wise budget allocation
- Budget vs. Actual spending comparison
- **2 Pie Charts**:
  - Budget Distribution
  - Current Month Expenses
- Progress tracking with visual indicators
- Expense limits and savings targets

### 5. **Anomaly Detection**
- AI-powered spending anomaly detection
- Real-time alerts for unusual transactions
- Anomaly history tracking

### 6. **AI Insights**
- Spending pattern analysis
- Month-over-month comparisons
- Category-wise spending insights
- Personalized recommendations
- Savings opportunities identification

### 7. **Theme Support**
- Light and Dark mode
- Persistent theme preference
- Optimized for readability in both modes

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18.3.1
- **Build Tool**: Vite 5.4.2
- **Styling**: Tailwind CSS 3.4.1
- **Charts**: Recharts 2.12.7
- **HTTP Client**: Axios 1.7.9
- **Date Handling**: date-fns 4.1.0
- **Icons**: Lucide React 0.469.0
- **Routing**: React Router DOM 7.1.1

### Backend
- **Framework**: FastAPI 0.115.0
- **Server**: Uvicorn 0.32.0 / Gunicorn 23.0.0
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT (python-jose 3.3.0)
- **Password Hashing**: Passlib with bcrypt
- **AI Integration**: Groq API 0.13.0
- **Validation**: Pydantic 2.10.3

### Deployment
- **Frontend**: Vercel
- **Backend**: Render
- **Database**: Supabase Cloud

---

## 🏗️ Architecture

### System Architecture
```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│                 │         │                  │         │                 │
│  React Frontend │◄───────►│  FastAPI Backend │◄───────►│  Supabase DB    │
│   (Vercel)      │  HTTPS  │    (Render)      │  SQL    │  (PostgreSQL)   │
│                 │         │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │
                                     │ API
                                     ▼
                            ┌──────────────────┐
                            │                  │
                            │   Groq AI API    │
                            │  (Budget & AI)   │
                            │                  │
                            └──────────────────┘
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Navbar.jsx
│   │   └── Footer.jsx
│   ├── context/           # React Context providers
│   │   ├── AuthContext.jsx
│   │   └── ThemeContext.jsx
│   ├── pages/             # Page components
│   │   ├── Login.jsx
│   │   ├── Signup.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Transactions.jsx
│   │   ├── Budget.jsx
│   │   ├── Insights.jsx
│   │   ├── Anomalies.jsx
│   │   └── Profile.jsx
│   ├── services/          # API service layer
│   │   └── api.js
│   ├── App.jsx            # Main app component
│   └── main.jsx           # Entry point
├── public/                # Static assets
└── package.json
```

### Backend Structure
```
backend/
├── main.py               # FastAPI application & routes
├── auth.py               # Authentication logic
├── database.py           # Database connection
├── config.py             # Configuration management
├── schemas.py            # Pydantic models
├── ai_service.py         # AI integration (Groq)
├── requirements.txt      # Python dependencies
└── migrations/           # Database migrations
```

---

## 📦 Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Supabase account
- Groq API key

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with required variables
```

---

## ⚙️ Configuration

### Environment Variables

#### Backend (.env)
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# JWT Configuration
SECRET_KEY=your-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Configuration
GROQ_API_KEY=your-groq-api-key

# Application Settings
APP_NAME=FinSage API
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production
```

#### Frontend (.env)
```env
VITE_API_URL=https://finsage-xabw.onrender.com
```

---

## 🚀 Deployment

### Frontend (Vercel)

1. **Connect Repository**:
   - Go to Vercel dashboard
   - Import GitHub repository: `cherry-10/FinSage`

2. **Configure Build Settings**:
   - Framework Preset: Vite
   - Build Command: `cd frontend && npm run build`
   - Output Directory: `frontend/dist`
   - Root Directory: `/`

3. **Environment Variables**:
   - Add `VITE_API_URL` with backend URL

4. **Deploy**: Vercel auto-deploys on push to main branch

### Backend (Render)

1. **Create Web Service**:
   - Connect GitHub repository
   - Runtime: Python 3

2. **Configure Settings**:
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
   - Root Directory: `/`

3. **Environment Variables**:
   - Add all backend environment variables from `.env`

4. **Deploy**: Render auto-deploys on push to main branch

### Database (Supabase)

1. **Create Project** on Supabase
2. **Run SQL Migration**:
```sql
-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash TEXT NOT NULL,
    profile_photo TEXT,
    annual_salary DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(15, 2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    transaction_type VARCHAR(20) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create budget table
CREATE TABLE budget (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    allocated_amount DECIMAL(15, 2) NOT NULL,
    priority VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create expense_limits table
CREATE TABLE expense_limits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    monthly_limit DECIMAL(15, 2) NOT NULL,
    target_savings DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create anomalies table
CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    transaction_id INTEGER REFERENCES transactions(id) ON DELETE CASCADE,
    anomaly_type VARCHAR(100),
    severity VARCHAR(20),
    description TEXT,
    detected_at TIMESTAMP DEFAULT NOW()
);

-- Create income table (optional)
CREATE TABLE income (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(15, 2) NOT NULL,
    source VARCHAR(100),
    date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create settings table
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    notifications_enabled BOOLEAN DEFAULT true,
    dark_mode BOOLEAN DEFAULT false,
    anomaly_alerts BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_budget_user_id ON budget(user_id);
CREATE INDEX idx_anomalies_user_id ON anomalies(user_id);
```

---

## 📚 API Documentation

### Base URL
```
Production: https://finsage-xabw.onrender.com
Development: http://localhost:8000
```

### Authentication Endpoints

#### POST `/api/auth/register`
Register a new user.

**Request Body**:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "1234567890",
  "password": "securepassword"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### POST `/api/auth/login`
Login with credentials.

**Request Body** (form-data):
```
username: john@example.com
password: securepassword
```

**Response**:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### GET `/api/auth/me`
Get current user information.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "1234567890",
  "annual_salary": 600000,
  "created_at": "2024-01-01T00:00:00"
}
```

### Transaction Endpoints

#### GET `/api/transactions`
Get all user transactions.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
[
  {
    "id": 1,
    "amount": 500,
    "category": "Food",
    "description": "Groceries",
    "transaction_type": "expense",
    "transaction_date": "2024-01-15T10:00:00",
    "created_at": "2024-01-15T10:00:00"
  }
]
```

#### POST `/api/transactions`
Create a new transaction.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "amount": 500,
  "category": "Food",
  "description": "Groceries",
  "transaction_type": "expense",
  "transaction_date": "2024-01-15T10:00:00"
}
```

#### DELETE `/api/transactions/{id}`
Delete a transaction.

**Headers**: `Authorization: Bearer <token>`

### Dashboard Endpoints

#### GET `/api/dashboard?period=current_month`
Get dashboard statistics.

**Query Parameters**:
- `period`: `current_month` or `last_month`

**Response**:
```json
{
  "total_income": 50000,
  "total_expenses": 30000,
  "savings": 20000,
  "anomaly_count": 2,
  "this_month_expenses": 30000,
  "last_month_expenses": 28000,
  "recent_transactions": [...],
  "category_breakdown": [
    {"category": "Food", "total": 5000},
    {"category": "Transport", "total": 3000}
  ]
}
```

#### GET `/api/dashboard/trends`
Get trend data for graphs.

**Response**:
```json
{
  "this_month_daily": [
    {"date": "01", "total": 500},
    {"date": "02", "total": 750}
  ],
  "last_month_daily": [...],
  "this_month_categories": [
    {"category": "Food", "total": 5000}
  ],
  "last_month_categories": [...]
}
```

### Budget Endpoints

#### POST `/api/budget/generate`
Generate AI-powered budget.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "categories": [
    {
      "category": "Rent",
      "allocated_amount": 15000,
      "priority": "high"
    }
  ]
}
```

#### GET `/api/budget`
Get current budget plan.

### Insights Endpoint

#### GET `/api/insights`
Get AI-powered financial insights.

**Response**:
```json
{
  "summary": "Based on your spending patterns...",
  "recommendations": [
    {
      "category": "Spending Alert",
      "message": "Your spending increased by...",
      "type": "warning"
    }
  ],
  "current_month_total": 30000,
  "last_month_total": 28000,
  "difference": 2000,
  "percent_change": 7.14
}
```

---

## 🗄️ Database Schema

### Users Table
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | VARCHAR(255) | User's full name |
| email | VARCHAR(255) | Unique email |
| phone | VARCHAR(20) | Phone number |
| password_hash | TEXT | Hashed password |
| profile_photo | TEXT | Profile photo URL |
| annual_salary | DECIMAL(15,2) | Annual income |
| created_at | TIMESTAMP | Account creation date |

### Transactions Table
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | INTEGER | Foreign key to users |
| amount | DECIMAL(15,2) | Transaction amount |
| category | VARCHAR(100) | Category name |
| description | TEXT | Transaction description |
| transaction_type | VARCHAR(20) | 'income' or 'expense' |
| transaction_date | TIMESTAMP | Transaction date |
| created_at | TIMESTAMP | Record creation date |

### Budget Table
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | INTEGER | Foreign key to users |
| category | VARCHAR(100) | Budget category |
| allocated_amount | DECIMAL(15,2) | Allocated budget |
| priority | VARCHAR(20) | Priority level |
| created_at | TIMESTAMP | Record creation date |

---

## 📖 Usage Guide

### Getting Started

1. **Register an Account**:
   - Visit the signup page
   - Enter name, email, phone, and password
   - Click "Create Account"

2. **Set Annual Salary**:
   - Go to Profile page
   - Enter your annual salary
   - This is used to calculate monthly income

3. **Add Transactions**:
   - Go to Transactions page
   - Click "Add Transaction"
   - Select type (Income/Expense)
   - Choose category
   - Enter amount and description
   - Save transaction

4. **Generate Budget**:
   - Go to Budget page
   - Click "Generate Smart Budget"
   - AI will create a budget based on your spending
   - Set expense limits and savings targets

5. **View Dashboard**:
   - Dashboard shows real-time analytics
   - Use month filters to compare periods
   - View graphs for spending trends

6. **Check Insights**:
   - Go to Insights page
   - View AI-powered recommendations
   - Track spending patterns
   - Get savings opportunities

### Categories

**Expense Categories**:
- Food
- Transport
- Shopping
- Entertainment
- Bills
- Rent
- Healthcare
- Education
- Other

**Income Categories**:
- Salary
- Bonus
- Incentives
- Freelance
- Investment
- Gift
- Other Income

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Slow Loading / Page Not Found After 1 Hour
**Cause**: Render free tier spins down after inactivity.

**Solution**:
- First request after inactivity takes 30-60 seconds
- Subsequent requests are fast
- Consider upgrading to paid tier for always-on service

#### 2. Login/Registration Fails
**Cause**: Backend not responding or JWT issues.

**Solutions**:
- Check if backend is running: Visit `https://finsage-xabw.onrender.com/health`
- Clear browser cache and cookies
- Check network tab for error details
- Verify `VITE_API_URL` is correct

#### 3. Dark Mode Text Not Visible
**Cause**: Missing dark mode text color classes.

**Solution**: Already fixed in latest version. Update to latest code.

#### 4. Dashboard Graphs Empty
**Cause**: No transactions or incorrect data filtering.

**Solutions**:
- Add some transactions first
- Check if transactions have correct dates
- Verify month filter is working

#### 5. Budget Generation Fails
**Cause**: Missing income or expense limits.

**Solutions**:
- Set annual salary in Profile
- Set expense limits in Budget page
- Ensure you have some transactions

### Development Issues

#### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt

# Check environment variables
# Ensure all required vars are set in .env
```

#### Frontend Build Fails
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is private and proprietary.

---

## 👥 Authors

- **Charan Teja** - Initial work

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- React and Vite for modern frontend development
- Supabase for database infrastructure
- Groq for AI capabilities
- Vercel and Render for deployment platforms

---

## 📞 Support

For issues and questions:
- GitHub Issues: https://github.com/cherry-10/FinSage/issues
- Email: support@finsage.com

---

**Last Updated**: January 2026
**Version**: 1.0.0
