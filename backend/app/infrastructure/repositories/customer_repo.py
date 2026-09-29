"""Customer repository.

All persistence operations for the Customer domain.  This module knows
about SQLAlchemy; the application layer (``CustomerService``) does not.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.customer.models import Customer


class CustomerRepository:
    """Data-access object for ``Customer`` records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, customer_id: uuid.UUID) -> Customer | None:
        """Return a customer by internal UUID, or ``None`` if not found."""
        return self._session.get(Customer, customer_id)

    def get_by_reference(self, reference: str) -> Customer | None:
        """Return a customer by human-friendly reference, or ``None``."""
        stmt = select(Customer).where(Customer.reference == reference)
        return self._session.scalars(stmt).first()

    def create(self, reference: str, name: str, phone: str, email: str) -> Customer:
        """Persist a new customer and flush so its ``id`` is populated.

        The caller is responsible for committing the surrounding
        transaction.
        """
        customer = Customer(
            id=uuid.uuid4(),
            reference=reference,
            name=name,
            phone=phone,
            email=email,
        )
        self._session.add(customer)
        self._session.flush()
        return customer
