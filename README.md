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

## Category endpoints

| Method | Path | Success status |
| --- | --- | --- |
| `GET` | `/categories` | `200` |
| `GET` | `/categories/{id}` | `200` |
| `POST` | `/categories` | `201` |
| `PUT` | `/categories/{id}` | `200` |
| `DELETE` | `/categories/{id}` | `204` |

Creating or renaming a category to a duplicate name returns `409 Conflict`.
Deleting a category that still has expenses also returns `409 Conflict` because
the request conflicts with the category's current state.

## Expense endpoints

| Method | Path | Success status |
| --- | --- | --- |
| `GET` | `/expenses` | `200` |
| `GET` | `/expenses/{id}` | `200` |
| `POST` | `/expenses` | `201` |
| `PUT` | `/expenses/{id}` | `200` |
| `DELETE` | `/expenses/{id}` | `204` |

The expense list accepts optional `category_id`, `from_date`, and `to_date`
query parameters. They can be used independently or together:

```text
GET /expenses?category_id=1&from_date=2026-03-01&to_date=2026-03-31
```

Expense responses contain the raw `category_id` and the nested category object.
