"""Support case application services."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.support_case import SupportCase
from app.infrastructure.repositories.support_case_repo import SupportCaseRepository
from app.infrastructure.repositories.transaction_repo import TransactionRepository


def create_support_case(
    session: Session,
    transaction_reference: str,
    message: str,
) -> SupportCase:
    transaction_repo = TransactionRepository(session)
    transaction = transaction_repo.get_by_reference(transaction_reference)

    if transaction is None:
        raise NotFoundError("Transaction not found")

    case_reference = f"CASE-{uuid4().hex[:8].upper()}"

    support_case = SupportCase(
        reference=case_reference,
        transaction_reference=transaction.reference,
        customer_id=transaction.customer_id,
        message=message,
        status="OPEN",
    )

    repository = SupportCaseRepository(session)
    return repository.create(support_case)


def get_support_case(
    session: Session,
    reference: str,
) -> SupportCase:
    repository = SupportCaseRepository(session)
    support_case = repository.get_by_reference(reference)

    if support_case is None:
        raise NotFoundError("Support case not found")

    return support_case


def investigate_support_case(
    session: Session,
    reference: str,
) -> SupportCase:
    repository = SupportCaseRepository(session)
    support_case = repository.get_by_reference(reference)

    if support_case is None:
        raise NotFoundError("Support case not found")

    transaction_repo = TransactionRepository(session)
    transaction = transaction_repo.get_by_reference(
        support_case.transaction_reference
    )

    if transaction is None:
        raise NotFoundError("Transaction not found")

    support_case.status = "RESOLVED"
    support_case.response = (
        f"We checked payment {transaction.reference}. "
        f"The current status is {transaction.status}. "
        f"The payment is recorded as {transaction.description.lower()}."
    )
    support_case.resolved_at = datetime.utcnow()

    session.commit()
    session.refresh(support_case)

    return support_case
