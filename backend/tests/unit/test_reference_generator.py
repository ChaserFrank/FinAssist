"""Unit tests for the reference generator.

Verifies format conventions, uniqueness within a session, and that
the SQLite fallback produces the correct prefix formats.
"""

from sqlalchemy.orm import Session

from app.infrastructure.database.reference_generator import (
    next_customer_reference,
    next_dispute_reference,
    next_support_case_reference,
    next_transaction_reference,
)


class TestReferenceFormats:
    def test_customer_reference_format(self, db_session: Session) -> None:
        ref = next_customer_reference(db_session)
        assert ref.startswith("CUS-")
        assert len(ref) > 4

    def test_transaction_reference_format(self, db_session: Session) -> None:
        ref = next_transaction_reference(db_session)
        assert ref.startswith("TXN-")

    def test_support_case_reference_format(self, db_session: Session) -> None:
        ref = next_support_case_reference(db_session)
        assert ref.startswith("CASE-")

    def test_dispute_reference_format(self, db_session: Session) -> None:
        ref = next_dispute_reference(db_session)
        assert ref.startswith("DSP-")


class TestReferenceUniqueness:
    def test_consecutive_customer_references_are_unique(self, db_session: Session) -> None:
        refs = {next_customer_reference(db_session) for _ in range(10)}
        assert len(refs) == 10

    def test_consecutive_dispute_references_are_unique(self, db_session: Session) -> None:
        refs = {next_dispute_reference(db_session) for _ in range(10)}
        assert len(refs) == 10
