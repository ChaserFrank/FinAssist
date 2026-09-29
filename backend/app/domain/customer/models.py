"""Customer domain model.

The Customer entity is the external person or business that interacts
with FinAssist through the payment support workflow.  Internal identity
is a UUID; the externally visible identifier is `reference` (e.g.
``CUS-10001``).  See ``docs/database.md`` and
``docs/decisions/004-reference-generation-and-dispute-integrity.md``
for the convention.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Customer(Base):
    """Persistent customer record."""

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    # Human-friendly external ID, e.g. CUS-10001.  Never exposed as a raw UUID.
    reference: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Customer {self.reference!r}>"
