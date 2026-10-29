from fastapi.testclient import TestClient


def test_frontend_is_served_at_root(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Expense Tracker" in response.text
    assert '<link rel="stylesheet" href="/styles.css">' in response.text
    assert '<script src="/app.js" defer></script>' in response.text


def test_frontend_assets_are_served(client: TestClient) -> None:
    script = client.get("/app.js")
    stylesheet = client.get("/styles.css")

    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")
