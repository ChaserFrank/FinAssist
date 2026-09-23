"""Application configuration.

Configuration is loaded from environment variables (and an optional .env
file during local development). Nothing in this module should contain a
real secret — see `.env.example` at the repository root for the documented
variable list.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the FinAssist backend.

    All fields have safe local-development defaults except DATABASE_URL,
    which must be provided (Docker Compose supplies it automatically).
    """

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

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+psycopg://finassist:finassist@localhost:5432/finassist"
    )

    # --- watsonx.ai (empty locally; populated once IBM TechZone is available) ---
    WATSONX_API_KEY: str = ""
    WATSONX_PROJECT_ID: str = ""
    WATSONX_URL: str = ""

    # --- Watson Orchestrate (empty locally) ---
    ORCHESTRATE_URL: str = ""
    ORCHESTRATE_API_KEY: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so environment variables are parsed once per process; tests can
    call `get_settings.cache_clear()` if they need to reload configuration.
    """
    return Settings()
