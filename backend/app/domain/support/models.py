"""Support case domain model.

A SupportCase is the customer-support tracking record opened whenever a
customer contacts FinAssist about a payment issue.  It may or may not
be linked to a specific Transaction.  When a formal Dispute is raised,
a SupportCase is always created first and the Dispute references it.

Internal identity is a UUID; externally visible identifier is
``reference`` (e.g. ``CASE-1042``).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.support.enums import SupportCaseStatus
from app.infrastructure.database.base import Base, status_check, status_enum


class SupportCase(Base):
    """Persistent support case record."""

    __tablename__ = "support_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    # Human-friendly external ID, e.g. CASE-1042.
    reference: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Optional: link to the transaction the customer is asking about.
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Short label for the type of issue, e.g. "payment_dispute", "status_inquiry".
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SupportCaseStatus] = mapped_column(
        status_enum(SupportCaseStatus),
        nullable=False,
        default=SupportCaseStatus.OPEN,
    )
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

    __table_args__ = (status_check("support_cases", SupportCaseStatus),)

    customer: Mapped["Customer"] = relationship("Customer", lazy="select")  # noqa: F821
    transaction: Mapped["Transaction | None"] = relationship(  # noqa: F821
        "Transaction", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<SupportCase {self.reference!r} status={self.status}>"
