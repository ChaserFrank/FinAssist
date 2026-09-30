"""Support case repository.

All persistence operations for the SupportCase domain.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.support.enums import SupportCaseStatus
from app.domain.support.models import SupportCase


class SupportCaseRepository:
    """Data-access object for ``SupportCase`` records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_reference(self, reference: str) -> SupportCase | None:
        """Return a support case by human-friendly reference, or ``None``."""
        stmt = select(SupportCase).where(SupportCase.reference == reference)
        return self._session.scalars(stmt).first()

    def create(
        self,
        reference: str,
        customer_id: uuid.UUID,
        category: str,
        description: str,
        transaction_id: uuid.UUID | None = None,
        status: SupportCaseStatus = SupportCaseStatus.OPEN,
    ) -> SupportCase:
        """Persist a new support case and flush so its ``id`` is populated.

        The caller is responsible for committing the surrounding
        transaction.
        """
        case = SupportCase(
            id=uuid.uuid4(),
            reference=reference,
            customer_id=customer_id,
            transaction_id=transaction_id,
            category=category,
            description=description,
            status=status,
        )
        self._session.add(case)
        self._session.flush()
        return case
