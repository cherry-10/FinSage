# FinSage Backend

FastAPI backend for the FinSage personal finance management application.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure database in `.env`:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/finsage
```

4. Run the server:
```bash
python main.py
```

Server runs on `http://localhost:8000`

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Database

Tables are created automatically on first run using SQLAlchemy.
