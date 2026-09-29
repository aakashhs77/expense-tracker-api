from fastapi.testclient import TestClient


def test_frontend_is_served_at_root(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Expense Tracker" in response.text
    assert 'fetchJson("/graphql"' in response.text
    assert 'fetchJson("/expenses"' in response.text
