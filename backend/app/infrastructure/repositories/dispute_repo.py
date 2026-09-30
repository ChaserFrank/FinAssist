"""Dispute repository.

All persistence operations for the Dispute domain.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.dispute.enums import DisputeStatus
from app.domain.dispute.models import Dispute


class DisputeRepository:
    """Data-access object for ``Dispute`` records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_reference(self, reference: str) -> Dispute | None:
        """Return a dispute by human-friendly reference, or ``None``."""
        stmt = select(Dispute).where(Dispute.reference == reference)
        return self._session.scalars(stmt).first()

    def find_active_by_transaction_id(self, transaction_id: uuid.UUID) -> Dispute | None:
        """Return the active (OPEN or UNDER_REVIEW) dispute for a transaction, if any.

        This is the application-level check that precedes the database-level
        partial unique index.  Both layers together prevent duplicate open
        disputes (see ADR-004).
        """
        stmt = select(Dispute).where(
            Dispute.transaction_id == transaction_id,
            Dispute.status.in_([DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW]),
        )
        return self._session.scalars(stmt).first()

    def create(
        self,
        reference: str,
        support_case_id: uuid.UUID,
        transaction_id: uuid.UUID,
        reason: str,
        status: DisputeStatus = DisputeStatus.OPEN,
    ) -> Dispute:
        """Persist a new dispute and flush so its ``id`` is populated.

        The caller is responsible for committing the surrounding
        transaction.  Note: ``support_case_id`` must be populated before
        this is called (i.e. the SupportCase must have been flushed first).
        """
        dispute = Dispute(
            id=uuid.uuid4(),
            reference=reference,
            support_case_id=support_case_id,
            transaction_id=transaction_id,
            reason=reason,
            status=status,
        )
        self._session.add(dispute)
        self._session.flush()
        return dispute
