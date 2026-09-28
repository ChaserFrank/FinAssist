"""Dispute application services."""

from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.dispute import Dispute
from app.domain.support_case import SupportCase
from app.infrastructure.repositories.customer_repo import CustomerRepository
from app.infrastructure.repositories.dispute_repo import DisputeRepository
from app.infrastructure.repositories.transaction_repo import TransactionRepository


def create_dispute(
    session: Session,
    customer_reference: str,
    transaction_reference: str,
    reason: str,
) -> Dispute:
    transaction_repository = TransactionRepository(session)
    customer_repository = CustomerRepository(session)
    dispute_repository = DisputeRepository(session)

    transaction = transaction_repository.get_by_reference(
        transaction_reference
    )
    customer = customer_repository.get_by_reference(customer_reference)

    if transaction is None:
        raise NotFoundError("Transaction not found")

    if customer is None:
        raise NotFoundError("Customer not found")

    if transaction.customer_id != customer.reference:
        raise ValueError("Customer is not authorized for this transaction")

    if transaction.status != "FAILED":
        raise ValueError(
            "A dispute can only be created for a failed transaction"
        )

    existing_dispute = dispute_repository.get_by_transaction_reference(
        transaction.reference
    )

    if existing_dispute is not None:
        raise ValueError("A dispute already exists for this transaction")

    case_reference = f"CASE-{uuid4().hex[:8].upper()}"

    support_case = SupportCase(
        reference=case_reference,
        transaction_reference=transaction.reference,
        customer_id=customer.reference,
        message=reason,
        status="OPEN",
    )

    session.add(support_case)
    session.flush()

    dispute_reference = f"DSP-{uuid4().hex[:8].upper()}"

    dispute = dispute_repository.create(
        reference=dispute_reference,
        support_case_reference=support_case.reference,
        transaction_reference=transaction.reference,
        reason=reason,
    )

    session.commit()
    session.refresh(dispute)

    return dispute