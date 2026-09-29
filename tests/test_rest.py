from fastapi.testclient import TestClient


def test_create_and_read_expense(client: TestClient) -> None:
    create_response = client.post(
        "/expenses",
        json={
            "amount": "25.50",
            "description": "Coffee beans",
            "spent_on": "2026-03-15",
            "category_id": 1,
        },
    )

    assert create_response.status_code == 201
    created_expense = create_response.json()
    assert created_expense["amount"] == "25.50"
    assert created_expense["category"] == {"id": 1, "name": "Food"}

    read_response = client.get(
        f"/expenses/{created_expense['id']}"
    )

    assert read_response.status_code == 200
    assert read_response.json() == created_expense


def test_filter_expenses_by_category_and_date(client: TestClient) -> None:
    response = client.get(
        "/expenses",
        params={
            "category_id": 1,
            "from_date": "2026-03-01",
            "to_date": "2026-03-31",
        },
    )

    assert response.status_code == 200
    expenses = response.json()
    assert [expense["description"] for expense in expenses] == [
        "Lunch",
        "Groceries",
    ]
    assert all(expense["category"]["name"] == "Food" for expense in expenses)


def test_negative_expense_amount_returns_422(client: TestClient) -> None:
    response = client.post(
        "/expenses",
        json={
            "amount": "-1.00",
            "description": "Invalid expense",
            "spent_on": "2026-03-15",
            "category_id": 1,
        },
    )

    assert response.status_code == 422


def test_missing_expense_returns_404(client: TestClient) -> None:
    response = client.get("/expenses/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Expense not found."}


def test_duplicate_category_returns_409(client: TestClient) -> None:
    response = client.post("/categories", json={"name": "Food"})

    assert response.status_code == 409
    assert response.json() == {
        "detail": "A category with this name already exists."
    }


def test_monthly_summary_calculation(client: TestClient) -> None:
    response = client.get("/summary", params={"month": "2026-03"})

    assert response.status_code == 200
    assert response.json() == {
        "month": "2026-03",
        "total_spend": "60.00",
        "categories": [
            {
                "category_name": "Food",
                "total": "50.00",
                "share_percentage": "83.33",
            },
            {
                "category_name": "Transport",
                "total": "10.00",
                "share_percentage": "16.67",
            },
        ],
    }
