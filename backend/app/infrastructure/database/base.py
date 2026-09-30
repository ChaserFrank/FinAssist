"""SQLAlchemy declarative base and shared column helpers.

All ORM models inherit from ``Base``. Kept separate from ``session.py`` to
avoid circular imports between models and engine/session setup.
"""

from enum import StrEnum

from sqlalchemy import CheckConstraint, Enum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def status_enum(enum_cls: type[StrEnum]) -> Enum:
    """Column type for a status enum.

    * Stored as a plain ``VARCHAR(16)`` (``native_enum=False``) rather than a
      native Postgres ENUM, so adding a status later is an ordinary migration
      instead of ``ALTER TYPE ... ADD VALUE`` (which cannot run inside a
      transaction).
    * Values round-trip as real enum members (not bare ``str``), so
      ``row.status.value`` is always safe.
    * ``validate_strings=True`` rejects an invalid status in Python before it
      ever reaches the database. The database-level ``CHECK`` constraint from
      ``status_check`` is the second, independent line of defence.
    """
    return Enum(
        enum_cls,
        native_enum=False,
        length=16,
        validate_strings=True,
        values_callable=lambda members: [m.value for m in members],
    )


def status_check(table: str, enum_cls: type[StrEnum]) -> CheckConstraint:
    """``CHECK (status IN (...))`` generated from the enum, so it can't drift."""
    values = ", ".join(f"'{m.value}'" for m in enum_cls)
    return CheckConstraint(f"status IN ({values})", name=f"ck_{table}_status")
