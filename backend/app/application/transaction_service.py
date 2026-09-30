"""Transaction use cases (application layer).

Business rules owned here:
- A transaction can only be retrieved by its reference.
- If the reference does not exist, TRANSACTION_NOT_FOUND is raised.

The TransactionService is used by routes and by DisputeService — keeping
the lookup logic in one place avoids duplication and ensures consistent
error handling regardless of the caller.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ErrorCode
from app.domain.transaction.models import Transaction
from app.infrastructure.repositories.customer_repo import CustomerRepository
from app.infrastructure.repositories.transaction_repo import TransactionRepository


class TransactionService:
    """Application-layer use cases for the Transaction domain."""

    def __init__(self, session: Session) -> None:
        self._repo = TransactionRepository(session)
        self._customer_repo = CustomerRepository(session)

    def get_transaction(self, reference: str) -> Transaction:
        """Return the transaction identified by ``reference``.

        Raises:
            AppError(TRANSACTION_NOT_FOUND): if no transaction with that
                reference exists in the database.
        """
        txn = self._repo.get_by_reference(reference)
        if txn is None:
            raise AppError(
                ErrorCode.TRANSACTION_NOT_FOUND,
                f"No transaction found with reference '{reference}'.",
            )
        return txn

    def get_transaction_for_customer(
        self, customer_reference: str, transaction_reference: str
    ) -> Transaction:
        """Return the transaction only if it belongs to ``customer_reference``.

        Used by the conversational flow, where the caller is acting *as* a
        customer. A transaction that exists but belongs to someone else is
        reported as ``TRANSACTION_NOT_FOUND`` with the same message as a
        genuinely missing one, so the endpoint cannot be used to discover
        which references exist.

        Raises:
            AppError(CUSTOMER_NOT_FOUND):    unknown customer.
            AppError(TRANSACTION_NOT_FOUND): missing *or* not owned by customer.
        """
        customer = self._customer_repo.get_by_reference(customer_reference)
        if customer is None:
            raise AppError(
                ErrorCode.CUSTOMER_NOT_FOUND,
                f"No customer found with reference '{customer_reference}'.",
            )
        txn = self._repo.get_by_reference(transaction_reference)
        if txn is None or txn.customer_id != customer.id:
            raise AppError(
                ErrorCode.TRANSACTION_NOT_FOUND,
                f"No transaction found with reference '{transaction_reference}' "
                "on your account.",
            )
        return txn
