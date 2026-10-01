"""Application configuration.

All configuration comes from environment variables (or a local, git-ignored
``.env`` file). **No credential, password, token or connection string with
embedded credentials may appear in this file or anywhere else in source
control** -- see ``docs/security.md`` and ``.env.example``.

Design notes
------------
* ``DATABASE_URL`` has *no default*. A missing value fails fast at startup
  with a clear validation error instead of silently connecting to whatever
  database a default happened to point at.
* Anything secret is a ``SecretStr`` so it renders as ``**********`` in
  reprs, logs and tracebacks. Call ``.get_secret_value()`` only at the exact
  point of use (engine creation, IBM client construction).
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the FinAssist backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Application ---
    APP_ENV: str = "local"
    APP_NAME: str = "FinAssist"
    LOG_LEVEL: str = "INFO"

    # Comma-separated list of browser origins allowed to call the API (CORS).
    # Defaults to the Vite dev server; set explicitly for any other deployment.
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # The public HTTPS URL this API is reachable at once deployed (e.g. an
    # Azure Container Apps or IBM Code Engine FQDN). Empty locally. When set,
    # it is published in the generated OpenAPI document's `servers` field
    # (see app/main.py) so anything importing that document -- watsonx
    # Orchestrate's OpenAPI tool import included -- knows the correct host
    # to call without the importer having to type it in by hand.
    API_PUBLIC_URL: str = ""

    # --- Database (required; no default on purpose) ---
    DATABASE_URL: SecretStr

    # --- watsonx.ai (empty locally; populated once IBM TechZone is available) ---
    WATSONX_API_KEY: SecretStr = SecretStr("")
    WATSONX_PROJECT_ID: str = ""
    WATSONX_URL: str = ""

    # --- Watson Orchestrate (empty locally) ---
    ORCHESTRATE_URL: str = ""
    ORCHESTRATE_API_KEY: SecretStr = SecretStr("")

    @property
    def cors_origin_list(self) -> list[str]:
        """``CORS_ORIGINS`` parsed into a clean list (blank entries dropped)."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (parsed once per process).

    Tests can call ``get_settings.cache_clear()`` to reload configuration.
    """
    return Settings()
