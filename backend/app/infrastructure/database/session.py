"""SQLAlchemy engine and session factory.

The engine is built from ``Settings.DATABASE_URL`` (a ``SecretStr``); the
raw value is unwrapped here and nowhere else.

``expire_on_commit=False``: sessions are short-lived (one per request) and
the API layer reads attributes of just-committed objects to build its
response. Keeping them loaded avoids a needless refresh query per object and
-- importantly -- makes production behave exactly like the test suite, which
uses the same setting.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL.get_secret_value(), pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)
