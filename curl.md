# Expense lifecycle with cURL

Start the API and seed the database before running these commands:

```bash
source .venv/bin/activate
python -m app.seed
fastapi dev app/main.py
```

Open a second terminal in the project directory. Set the API address and use
the seeded Food category:

```bash
BASE_URL="http://127.0.0.1:8000"
CATEGORY_ID=1
```

## 1. Create an expense

```bash
CREATE_RESPONSE=$(curl -sS -X POST "$BASE_URL/expenses" \
  -H "Content-Type: application/json" \
  -d "{\
    \"amount\": \"125.50\",\
    \"description\": \"Coffee beans\",\
    \"spent_on\": \"2026-03-20\",\
    \"category_id\": $CATEGORY_ID\
  }")

echo "$CREATE_RESPONSE"
EXPENSE_ID=$(printf '%s' "$CREATE_RESPONSE" | \
  python -c 'import json, sys; print(json.load(sys.stdin)["id"])')
echo "Created expense ID: $EXPENSE_ID"
```

## 2. Fetch the expense

```bash
curl -sS "$BASE_URL/expenses/$EXPENSE_ID"
```

## 3. Update the expense

```bash
curl -sS -X PUT "$BASE_URL/expenses/$EXPENSE_ID" \
  -H "Content-Type: application/json" \
  -d "{\
    \"amount\": \"150.75\",\
    \"description\": \"Coffee beans and filters\",\
    \"spent_on\": \"2026-03-21\",\
    \"category_id\": $CATEGORY_ID\
  }"
```

## 4. Delete the expense

```bash
curl -i -X DELETE "$BASE_URL/expenses/$EXPENSE_ID"
```

The delete request should return `HTTP/1.1 204 No Content`.
