"""Transaction domain model.

A Transaction is a single payment event associated with a Customer.
Internal identity is a UUID; the externally visible identifier is
``reference`` (e.g. ``TXN-84721``).  The ``status`` field uses a
controlled enum — workflow and eligibility logic depend on a
predictable, finite state set.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.transaction.enums import TransactionStatus
from app.infrastructure.database.base import Base, status_check, status_enum


class Transaction(Base):
    """Persistent transaction record."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    # Human-friendly external ID, e.g. TXN-84721.
    reference: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Monetary amount stored as fixed-precision decimal (12 digits, 2 decimal places).
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2), nullable=False)
    # ISO 4217 currency code, e.g. "KES", "USD".
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        status_enum(TransactionStatus),
        nullable=False,
        default=TransactionStatus.PENDING,
    )
    # Free-form label for the payment method, e.g. "M-Pesa", "card".
    payment_method: Mapped[str] = mapped_column(String(64), nullable=False)
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

    __table_args__ = (status_check("transactions", TransactionStatus),)

    # Relationships (lazy by default; loaded explicitly when needed)
    customer: Mapped["Customer"] = relationship("Customer", lazy="select")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Transaction {self.reference!r} status={self.status}>"
