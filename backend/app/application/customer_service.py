"""Customer use cases (application layer)."""

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ErrorCode
from app.domain.customer.models import Customer
from app.infrastructure.repositories.customer_repo import CustomerRepository


class CustomerService:
    """Read-only customer lookups (customers are provisioned out-of-band)."""

    def __init__(self, session: Session) -> None:
        self._repo = CustomerRepository(session)

    def get_customer(self, reference: str) -> Customer:
        """Return the customer with ``reference``.

        Raises:
            AppError(CUSTOMER_NOT_FOUND): if no such customer exists.
        """
        customer = self._repo.get_by_reference(reference)
        if customer is None:
            raise AppError(
                ErrorCode.CUSTOMER_NOT_FOUND,
                f"No customer found with reference '{reference}'.",
            )
        return customer
