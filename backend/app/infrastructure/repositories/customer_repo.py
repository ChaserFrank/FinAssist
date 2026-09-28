"""Persistence operations for customers."""

from sqlalchemy.orm import Session

from app.domain.customer import Customer


class CustomerRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_reference(self, reference: str) -> Customer | None:
        return (
            self.session.query(Customer)
            .filter(Customer.reference == reference.upper())
            .first()
        )