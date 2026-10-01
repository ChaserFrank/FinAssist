"""Configuration must fail fast, hold no defaults for secrets, and never print them."""

import secrets

import pytest
from pydantic import ValidationError

from app.config import Settings

# Generated at runtime, not a literal in source -- a hard-coded-looking
# string assigned to a password-shaped variable is exactly the pattern our
# own scanner (and GitGuardian) are built to catch, disguised or not.
_FAKE_PW = secrets.token_hex(12)
_FAKE_URL = f"postgresql+psycopg://user:{_FAKE_PW}@localhost/db"


def test_database_url_is_required_and_has_no_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None)
    assert "DATABASE_URL" in str(exc.value)


def test_secret_values_are_not_revealed_in_repr_or_str(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", _FAKE_URL)
    fake_api_key = secrets.token_hex(10)
    monkeypatch.setenv("WATSONX_API_KEY", fake_api_key)
    settings = Settings(_env_file=None)

    rendered = repr(settings) + str(settings) + str(settings.model_dump())
    assert _FAKE_PW not in rendered
    assert fake_api_key not in rendered
    # ...but the real value is still available where it is actually needed.
    assert settings.DATABASE_URL.get_secret_value() == _FAKE_URL


def test_ibm_settings_default_to_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    for name in ("WATSONX_API_KEY", "ORCHESTRATE_API_KEY", "WATSONX_URL", "ORCHESTRATE_URL"):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(_env_file=None)
    assert settings.WATSONX_API_KEY.get_secret_value() == ""
    assert settings.ORCHESTRATE_API_KEY.get_secret_value() == ""


def test_cors_origins_parsed_and_blank_entries_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("CORS_ORIGINS", " http://a.test , ,http://b.test,")
    assert Settings(_env_file=None).cors_origin_list == ["http://a.test", "http://b.test"]


def test_api_public_url_defaults_to_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.delenv("API_PUBLIC_URL", raising=False)
    assert Settings(_env_file=None).API_PUBLIC_URL == ""


def test_api_public_url_is_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("API_PUBLIC_URL", "https://finassist-backend.example.azurecontainerapps.io")
    settings = Settings(_env_file=None)
    assert settings.API_PUBLIC_URL == "https://finassist-backend.example.azurecontainerapps.io"
