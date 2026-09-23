"""SQLAlchemy declarative base.

All ORM models (once domain persistence is implemented) will inherit from
`Base`. Kept separate from `session.py` to avoid circular imports between
models and the engine/session setup.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
