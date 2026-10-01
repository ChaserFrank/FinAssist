"""The OpenAPI document's `servers` field must reflect API_PUBLIC_URL.

watsonx Orchestrate's OpenAPI tool import (and any other OpenAPI consumer)
uses this field to know which host to actually call -- see docs/ai.md and
docs/deployment-azure.md. Without it, FastAPI omits `servers` entirely and
the importer has to be told the host by hand, which is easy to get wrong.
"""

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def reload_app(monkeypatch: pytest.MonkeyPatch):
    """Reload app.main with a fresh Settings cache for each case.

    Needed because `app.config.get_settings` is `lru_cache`d and `app.main`
    builds the FastAPI instance (and its `servers` list) once at import
    time -- both must be re-evaluated per test to see a changed env var.
    """

    def _reload():
        import app.config
        import app.main

        app.config.get_settings.cache_clear()
        importlib.reload(app.main)
        return app.main.app

    yield _reload

    import app.config

    app.config.get_settings.cache_clear()


def test_no_servers_field_when_api_public_url_unset(monkeypatch, reload_app) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.delenv("API_PUBLIC_URL", raising=False)
    app = reload_app()

    schema = TestClient(app).get("/openapi.json").json()

    assert "servers" not in schema or schema["servers"] == []


def test_servers_field_set_from_api_public_url(monkeypatch, reload_app) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("API_PUBLIC_URL", "https://finassist-backend.example.azurecontainerapps.io")
    app = reload_app()

    schema = TestClient(app).get("/openapi.json").json()

    assert schema["servers"] == [
        {
            "url": "https://finassist-backend.example.azurecontainerapps.io",
            "description": "local",
        }
    ]
