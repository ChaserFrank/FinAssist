"""Persistence operations for disputes."""

from sqlalchemy.orm import Session

from app.domain.dispute import Dispute


class DisputeRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        reference: str,
        support_case_reference: str,
        transaction_reference: str,
        reason: str,
    ) -> Dispute:
        dispute = Dispute(
            reference=reference,
            support_case_reference=support_case_reference,
            transaction_reference=transaction_reference,
            reason=reason,
        )
        self.session.add(dispute)
        self.session.flush()
        return dispute

    def get_by_reference(self, reference: str) -> Dispute | None:
        return (
            self.session.query(Dispute)
            .filter(Dispute.reference == reference.upper())
            .first()
        )

    def get_by_transaction_reference(
        self,
        transaction_reference: str,
    ) -> Dispute | None:
        return (
            self.session.query(Dispute)
            .filter(
                Dispute.transaction_reference
                == transaction_reference.upper()
            )
            .first()
        )