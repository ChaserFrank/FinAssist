"""Transaction application services."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.transaction.models import Transaction
from app.infrastructure.repositories.customer_repo import CustomerRepository
from app.infrastructure.repositories.transaction_repo import TransactionRepository


def get_transaction(session: Session, reference: str) -> Transaction:
    repository = TransactionRepository(session)
    transaction = repository.get_by_reference(reference)

    if transaction is None:
        raise NotFoundError("Transaction not found")

    return transaction


def verify_transaction_customer(
    session: Session,
    transaction_reference: str,
    customer_reference: str,
) -> bool:
    transaction_repository = TransactionRepository(session)
    customer_repository = CustomerRepository(session)

    transaction = transaction_repository.get_by_reference(
        transaction_reference
    )
    customer = customer_repository.get_by_reference(customer_reference)

    if transaction is None:
        raise NotFoundError("Transaction not found")

    if customer is None:
        raise NotFoundError("Customer not found")

    return transaction.customer_id == customer.reference