"""Persistence operations for support cases."""

from sqlalchemy.orm import Session

from app.domain.support_case import SupportCase


class SupportCaseRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, support_case: SupportCase) -> SupportCase:
        self.session.add(support_case)
        self.session.commit()
        self.session.refresh(support_case)
        return support_case

    def get_by_reference(self, reference: str) -> SupportCase | None:
        return (
            self.session.query(SupportCase)
            .filter(SupportCase.reference == reference.upper())
            .first()
        )
