"""Transaction repository.

All persistence operations for the Transaction domain.  This module knows
about SQLAlchemy; the application layer does not.
"""

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.transaction.enums import TransactionStatus
from app.domain.transaction.models import Transaction


class TransactionRepository:
    """Data-access object for ``Transaction`` records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_reference(self, reference: str) -> Transaction | None:
        """Return a transaction by human-friendly reference, or ``None``."""
        stmt = select(Transaction).where(Transaction.reference == reference)
        return self._session.scalars(stmt).first()

    def get_by_customer_id(self, customer_id: uuid.UUID) -> list[Transaction]:
        """Return all transactions belonging to a customer."""
        stmt = select(Transaction).where(Transaction.customer_id == customer_id)
        return list(self._session.scalars(stmt).all())

    def create(
        self,
        reference: str,
        customer_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        status: TransactionStatus,
        payment_method: str,
    ) -> Transaction:
        """Persist a new transaction and flush so its ``id`` is populated.

        The caller is responsible for committing the surrounding
        transaction.
        """
        txn = Transaction(
            id=uuid.uuid4(),
            reference=reference,
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            status=status,
            payment_method=payment_method,
        )
        self._session.add(txn)
        self._session.flush()
        return txn
