"""Fixtures for tests that need a real PostgreSQL.

Configuration
-------------
``TEST_DATABASE_URL``  connection URL of a *dedicated, disposable* database.
                       Deliberately NOT ``DATABASE_URL``: these tests write and
                       delete rows, so they must never be pointed at a dev DB
                       by accident. As a second guard the database name must
                       end in ``_test``.
``REQUIRE_INTEGRATION=1``  (set in CI) turn "Postgres unavailable" from a silent
                       skip into a hard failure, so the tests that protect the
                       database-level guarantees can never quietly stop running.

The schema is built by running the real Alembic migrations (not
``create_all``), so migrations are exercised too.
"""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _unavailable(reason: str) -> None:
    if os.environ.get("REQUIRE_INTEGRATION") == "1":
        pytest.fail(f"Integration tests are required but cannot run: {reason}")
    pytest.skip(reason)


def alembic_config(url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return cfg


@pytest.fixture(scope="session")
def pg_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        _unavailable("TEST_DATABASE_URL is not set")
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql":
        _unavailable("TEST_DATABASE_URL is not a PostgreSQL URL")
    if not (parsed.database or "").endswith("_test"):
        pytest.fail(
            "Refusing to run: the TEST_DATABASE_URL database name must end in '_test' "
            "(these tests insert and delete rows)."
        )
    return url


@pytest.fixture(scope="session")
def pg_engine(pg_url: str) -> Generator[Engine, None, None]:
    engine = create_engine(pg_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        engine.dispose()
        _unavailable(f"PostgreSQL not reachable: {type(exc).__name__}")
    # Start from a clean schema, then apply the real migrations.
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    command.upgrade(alembic_config(pg_url), "head")
    yield engine
    engine.dispose()


@pytest.fixture()
def pg_session(pg_engine: Engine) -> Generator[Session, None, None]:
    session = sessionmaker(bind=pg_engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
