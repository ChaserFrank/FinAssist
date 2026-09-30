"""Support case use cases (application layer).

Business rules owned here:
- A support case requires a valid customer (by reference).
- If a transaction reference is provided, the transaction must exist.
- The customer must own the transaction (if one is provided).
- Retrieval by reference raises SUPPORT_CASE_NOT_FOUND if missing.

This service owns the transaction boundary for writes (ADR-006): it commits on
success and rolls back on any failure.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ErrorCode
from app.domain.support.models import SupportCase
from app.infrastructure.database.reference_generator import next_support_case_reference
from app.infrastructure.repositories.customer_repo import CustomerRepository
from app.infrastructure.repositories.support_case_repo import SupportCaseRepository
from app.infrastructure.repositories.transaction_repo import TransactionRepository


class SupportService:
    """Application-layer use cases for the SupportCase domain."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._case_repo = SupportCaseRepository(session)
        self._customer_repo = CustomerRepository(session)
        self._txn_repo = TransactionRepository(session)

    def create_case(
        self,
        customer_reference: str,
        category: str,
        description: str,
        transaction_reference: str | None = None,
    ) -> SupportCase:
        """Open a new support case.

        Args:
            customer_reference:    The ``CUS-xxxxx`` reference of the customer.
            category:              Short label (e.g. ``"payment_dispute"``).
            description:           Full description from the customer.
            transaction_reference: Optional ``TXN-xxxxx`` if the case relates
                                   to a specific transaction.

        Returns:
            The newly created ``SupportCase``.

        Raises:
            AppError(CUSTOMER_NOT_FOUND): customer reference does not exist.
            AppError(TRANSACTION_NOT_FOUND): transaction reference does not exist.
            AppError(CUSTOMER_TRANSACTION_MISMATCH): transaction exists but
                does not belong to the given customer.
        """
        customer = self._customer_repo.get_by_reference(customer_reference)
        if customer is None:
            raise AppError(
                ErrorCode.CUSTOMER_NOT_FOUND,
                f"No customer found with reference '{customer_reference}'.",
            )

        transaction_id = None
        if transaction_reference is not None:
            txn = self._txn_repo.get_by_reference(transaction_reference)
            if txn is None:
                raise AppError(
                    ErrorCode.TRANSACTION_NOT_FOUND,
                    f"No transaction found with reference '{transaction_reference}'.",
                )
            if txn.customer_id != customer.id:
                raise AppError(
                    ErrorCode.CUSTOMER_TRANSACTION_MISMATCH,
                    f"Transaction '{transaction_reference}' does not belong to "
                    f"customer '{customer_reference}'.",
                )
            transaction_id = txn.id

        try:
            case = self._case_repo.create(
                reference=next_support_case_reference(self._session),
                customer_id=customer.id,
                category=category,
                description=description,
                transaction_id=transaction_id,
            )
            self._session.commit()
            return case
        except Exception:
            self._session.rollback()
            raise

    def get_case(self, reference: str) -> SupportCase:
        """Return the support case identified by ``reference``.

        Raises:
            AppError(SUPPORT_CASE_NOT_FOUND): if not found.
        """
        case = self._case_repo.get_by_reference(reference)
        if case is None:
            raise AppError(
                ErrorCode.SUPPORT_CASE_NOT_FOUND,
                f"No support case found with reference '{reference}'.",
            )
        return case

    def get_case_for_customer(self, customer_reference: str, case_reference: str) -> SupportCase:
        """Return the case only if it belongs to ``customer_reference``.

        As with transactions, "exists but belongs to someone else" is reported
        exactly like "does not exist".

        Raises:
            AppError(CUSTOMER_NOT_FOUND):     unknown customer.
            AppError(SUPPORT_CASE_NOT_FOUND): missing *or* not owned by customer.
        """
        customer = self._customer_repo.get_by_reference(customer_reference)
        if customer is None:
            raise AppError(
                ErrorCode.CUSTOMER_NOT_FOUND,
                f"No customer found with reference '{customer_reference}'.",
            )
        case = self._case_repo.get_by_reference(case_reference)
        if case is None or case.customer_id != customer.id:
            raise AppError(
                ErrorCode.SUPPORT_CASE_NOT_FOUND,
                f"No support case found with reference '{case_reference}' on your account.",
            )
        return case
