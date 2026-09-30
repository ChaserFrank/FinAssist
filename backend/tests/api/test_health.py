"""API test for the /health endpoint.

Runs without any external services (no database required) — see
docs/development.md for why the health check is kept infrastructure-free.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
