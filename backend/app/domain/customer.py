"""Customer domain model."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )