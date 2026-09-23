"""Shared FastAPI dependencies (DI providers).

This module will host things like the DB session dependency and, later,
authentication/authorization dependencies once those concerns exist.
Intentionally empty in the foundation stage beyond the placeholder below.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.infrastructure.database.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for the lifetime of a single request.

    Not yet wired into any route — no route requires database access
    in the foundation stage.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
