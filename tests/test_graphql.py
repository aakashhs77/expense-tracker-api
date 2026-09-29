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
