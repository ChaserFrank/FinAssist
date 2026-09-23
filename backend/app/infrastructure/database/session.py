"""SQLAlchemy engine and session factory.

This module establishes the connection to PostgreSQL. It does not define
any domain tables — those are added once the domain schema is finalized
and introduced via Alembic migrations.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
