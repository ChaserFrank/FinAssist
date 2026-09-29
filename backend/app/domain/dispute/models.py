"""Dispute domain model.

A Dispute is a formal challenge raised against a specific Transaction.
It is always paired with a SupportCase (the customer service record),
which is created atomically in the same database transaction.

Internal identity is a UUID; externally visible identifier is
``reference`` (e.g. ``DSP-1042``).

Duplicate-open-dispute prevention is enforced at two levels:

1. Application level: ``DisputeService`` queries for any existing dispute
   with ``status IN ('OPEN', 'UNDER_REVIEW')`` before inserting.
2. Database level: a partial unique index (``uq_disputes_open_per_transaction``)
   prevents concurrent races from producing two active disputes for the
   same transaction.  Any constraint violation is caught and mapped to
   ``ErrorCode.DISPUTE_NOT_ELIGIBLE``.

See ``docs/decisions/004-reference-generation-and-dispute-integrity.md``.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.dispute.enums import DisputeStatus
from app.infrastructure.database.base import Base, status_check, status_enum

# Predicate shared by the partial unique index: a dispute is "active" while it
# is OPEN or UNDER_REVIEW. Built from the enum so it cannot drift from it.
_ACTIVE_PREDICATE = text(
    f"status IN ('{DisputeStatus.OPEN.value}', '{DisputeStatus.UNDER_REVIEW.value}')"
)


class Dispute(Base):
    """Persistent dispute record."""

    __tablename__ = "disputes"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    # Human-friendly external ID, e.g. DSP-1042.
    reference: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    support_case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("support_cases.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(
        status_enum(DisputeStatus),
        nullable=False,
        default=DisputeStatus.OPEN,
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

    support_case: Mapped["SupportCase"] = relationship("SupportCase", lazy="select")  # noqa: F821
    transaction: Mapped["Transaction"] = relationship("Transaction", lazy="select")  # noqa: F821

    # ---------------------------------------------------------------------------
    # Partial unique index — prevents more than one OPEN or UNDER_REVIEW dispute
    # per transaction at the database level, complementing the application-level
    # check in DisputeService.  Both PostgreSQL and SQLite (>= 3.8.0) support
    # partial indexes.
    # ---------------------------------------------------------------------------
    __table_args__ = (
        Index(
            "uq_disputes_open_per_transaction",
            "transaction_id",
            unique=True,
            postgresql_where=_ACTIVE_PREDICATE,
            sqlite_where=_ACTIVE_PREDICATE,
        ),
        status_check("disputes", DisputeStatus),
    )

    def __repr__(self) -> str:
        return f"<Dispute {self.reference!r} status={self.status}>"
