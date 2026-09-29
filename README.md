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

## Monthly summary

```text
GET /summary?month=2026-03
```

The response contains the month's total spend and a category breakdown with
each category's total and percentage share. A missing month or a value that
does not exactly match `YYYY-MM` returns `400 Bad Request`.

## GraphQL

Strawberry's GraphiQL interface is available at
<http://127.0.0.1:8000/graphql>. The schema provides the `expenses` and
`categories` queries plus the `addExpense` and `deleteExpense` mutations.

GraphQL uses camelCase names. This query fetches every category name and only
the amounts of its expenses:

```graphql
query CategoryExpenseAmounts {
  categories {
    name
    expenses {
      amount
    }
  }
}
```

The nested data is returned in one request. With the REST API, a client would
first fetch the categories and then make a filtered expense request for each
category, while also receiving fields it did not need.

Expenses can be filtered with the same values as REST:

```graphql
query MarchFoodExpenses {
  expenses(
    categoryId: 1
    fromDate: "2026-03-01"
    toDate: "2026-03-31"
  ) {
    id
    amount
    description
    spentOn
    category {
      name
    }
  }
}
```

Example mutation:

```graphql
mutation AddExpense {
  addExpense(
    input: {
      amount: "12.50"
      description: "Coffee"
      spentOn: "2026-03-21"
      categoryId: 1
    }
  ) {
    id
    amount
    category {
      name
    }
  }
}
```

## Automated tests

The test suite uses `test_expense_tracker.db`, resets its data before every
test, and overrides FastAPI's `get_db` dependency. The development database is
not used by either the REST or GraphQL tests.

```bash
pytest
```

The suite covers expense creation, reading and filtering, validation errors,
missing resources, duplicate categories, monthly summary calculations, and
GraphQL query and mutation responses.

## Manual API collections

Import
`postman/Expense_Tracker_API.postman_collection.json` into Postman. Start the
API with a freshly seeded database, then run the collection in its saved order.
It covers every REST resource with success and error cases.

See `curl.md` for a complete create, fetch, update, and delete expense
lifecycle using cURL.
