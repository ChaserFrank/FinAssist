"""Transaction application services."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.transaction.models import Transaction
from app.infrastructure.repositories.transaction_repo import TransactionRepository


def get_transaction(session: Session, reference: str) -> Transaction:
    repository = TransactionRepository(session)
    transaction = repository.get_by_reference(reference)

    if transaction is None:
        raise NotFoundError("Transaction not found")

    return transaction
