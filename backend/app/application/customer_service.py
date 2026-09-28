"""Customer application services."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.customer import Customer
from app.infrastructure.repositories.customer_repo import CustomerRepository


def get_customer(
    session: Session,
    reference: str,
) -> Customer:
    repository = CustomerRepository(session)
    customer = repository.get_by_reference(reference)

    if customer is None:
        raise NotFoundError("Customer not found")

    return customer