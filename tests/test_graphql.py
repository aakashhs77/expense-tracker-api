from fastapi.testclient import TestClient


def test_graphql_categories_query(client: TestClient) -> None:
    response = client.post(
        "/graphql",
        json={
            "query": """
                query {
                  categories {
                    name
                    expenses {
                      amount
                    }
                  }
                }
            """
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body
    assert body["data"]["categories"][0] == {
        "name": "Food",
        "expenses": [
            {"amount": "12.50"},
            {"amount": "37.50"},
            {"amount": "20.00"},
        ],
    }


def test_graphql_add_expense_mutation(client: TestClient) -> None:
    response = client.post(
        "/graphql",
        json={
            "query": """
                mutation AddExpense($input: AddExpenseInput!) {
                  addExpense(input: $input) {
                    id
                    amount
                    description
                    spentOn
                    category {
                      name
                    }
                  }
                }
            """,
            "variables": {
                "input": {
                    "amount": "15.75",
                    "description": "GraphQL coffee",
                    "spentOn": "2026-03-20",
                    "categoryId": 1,
                }
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body
    assert body["data"]["addExpense"] == {
        "id": 5,
        "amount": "15.75",
        "description": "GraphQL coffee",
        "spentOn": "2026-03-20",
        "category": {"name": "Food"},
    }


def test_category_expenses_load_only_when_requested_and_are_batched(client: TestClient) -> None:
    from sqlalchemy import event

    from app.database import engine

    statements: list[str] = []

    def record_select(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", record_select)
    try:
        response = client.post(
            "/graphql", json={"query": "{ categories { id name } }"},
        )
        assert "errors" not in response.json()
        assert len(statements) == 1
        assert "expenses" not in statements[0]

        statements.clear()
        response = client.post(
            "/graphql",
            json={"query": """
                { categories { name history: expenses { id spentOn } } }
            """},
        )
        body = response.json()
        assert "errors" not in body
        assert len(statements) == 2
        assert body["data"]["categories"] == [
            {"name": "Food", "history": [
                {"id": 1, "spentOn": "2026-03-05"},
                {"id": 2, "spentOn": "2026-03-10"},
                {"id": 4, "spentOn": "2026-04-02"},
            ]},
            {"name": "Transport", "history": [{"id": 3, "spentOn": "2026-03-08"}]},
            {"name": "Rent", "history": []},
        ]

        statements.clear()
        response = client.post(
            "/graphql",
            json={"query": """
                query($include: Boolean!) {
                    categories { name expenses @include(if: $include) { id } }
                }
            """, "variables": {"include": False}},
        )
        assert "errors" not in response.json()
        assert len(statements) == 1
    finally:
        event.remove(engine, "before_cursor_execute", record_select)
