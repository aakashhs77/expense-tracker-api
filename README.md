# Expense Tracker API

A personal expense tracker exposed through REST and GraphQL from one FastAPI application.

## Local setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m app.seed
fastapi dev app/main.py
```

The development server runs at <http://127.0.0.1:8000>. FastAPI's interactive REST documentation is available at <http://127.0.0.1:8000/docs>.

Running the seed command again does not duplicate data. It exits when it detects existing categories or expenses.

