"""Persistence operations for transactions."""

from sqlalchemy.orm import Session

from app.domain.transaction.models import Transaction


class TransactionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_reference(self, reference: str) -> Transaction | None:
        return (
            self.session.query(Transaction)
            .filter(Transaction.reference == reference.upper())
            .first()
        )
