"""Unit tests for dispute eligibility rules in DisputeService.

All business rules from the eligibility matrix (ADR-005) and the duplicate-
dispute rules (ADR-004) are covered here without any HTTP layer.
"""

import pytest
from sqlalchemy.orm import Session

from app.application.dispute_service import DisputeService
from app.core.exceptions import AppError, ErrorCode
from app.domain.dispute.enums import DisputeStatus
from app.domain.transaction.enums import TransactionStatus
from tests.conftest import make_customer, make_dispute, make_support_case, make_transaction

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _service(session: Session) -> DisputeService:
    return DisputeService(session)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestCreateDisputeSuccess:
    def test_success_transaction_creates_dispute(self, db_session: Session) -> None:
        customer = make_customer(db_session)
        txn = make_transaction(db_session, customer, status=TransactionStatus.SUCCESS)

        dispute = _service(db_session).create_dispute(
            customer.reference, txn.reference, "Unauthorised charge"
        )

        assert dispute.reference.startswith("DSP-")
        assert dispute.status == DisputeStatus.OPEN
        assert dispute.support_case is not None
        assert dispute.support_case.reference.startswith("CASE-")

    def test_failed_transaction_creates_dispute(self, db_session: Session) -> None:
        """FAILED transactions are the core FinAssist scenario (charged but failed)."""
        customer = make_customer(db_session)
        txn = make_transaction(
            db_session, customer, reference="TXN-84722", status=TransactionStatus.FAILED
        )

        dispute = _service(db_session).create_dispute(
            customer.reference, txn.reference, "Charged but payment failed"
        )

        assert dispute.status == DisputeStatus.OPEN


# ---------------------------------------------------------------------------
# Transaction not found
# ---------------------------------------------------------------------------

class TestTransactionNotFound:
    def test_raises_transaction_not_found(self, db_session: Session) -> None:
        customer = make_customer(db_session)

        with pytest.raises(AppError) as exc_info:
            _service(db_session).create_dispute(
                customer.reference, "TXN-99999", "Some reason"
            )

        assert exc_info.value.code == ErrorCode.TRANSACTION_NOT_FOUND


# ---------------------------------------------------------------------------
# Customer not found
# ---------------------------------------------------------------------------

class TestCustomerNotFound:
    def test_raises_customer_not_found(self, db_session: Session) -> None:
        customer = make_customer(db_session)
        txn = make_transaction(db_session, customer)

        with pytest.raises(AppError) as exc_info:
            _service(db_session).create_dispute(
                "CUS-99999", txn.reference, "Some reason"
            )

        assert exc_info.value.code == ErrorCode.CUSTOMER_NOT_FOUND


# ---------------------------------------------------------------------------
# Customer-transaction mismatch
# ---------------------------------------------------------------------------

class TestCustomerTransactionMismatch:
    def test_raises_mismatch_when_txn_belongs_to_other_customer(
        self, db_session: Session
    ) -> None:
        alice = make_customer(db_session, reference="CUS-10001")
        bob = make_customer(db_session, reference="CUS-10002", name="Bob")
        # Transaction belongs to Alice
        txn = make_transaction(db_session, alice)

        # Bob attempts to dispute Alice's transaction
        with pytest.raises(AppError) as exc_info:
            _service(db_session).create_dispute(
                bob.reference, txn.reference, "Not my charge"
            )

        assert exc_info.value.code == ErrorCode.CUSTOMER_TRANSACTION_MISMATCH


# ---------------------------------------------------------------------------
# Invalid transaction state — PENDING
# ---------------------------------------------------------------------------

class TestPendingTransactionIneligible:
    def test_pending_raises_invalid_state(self, db_session: Session) -> None:
        customer = make_customer(db_session)
        txn = make_transaction(
            db_session, customer, reference="TXN-84723", status=TransactionStatus.PENDING
        )

        with pytest.raises(AppError) as exc_info:
            _service(db_session).create_dispute(
                customer.reference, txn.reference, "Still pending"
            )

        err = exc_info.value
        assert err.code == ErrorCode.INVALID_TRANSACTION_STATE
        assert "pending" in err.message.lower()


# ---------------------------------------------------------------------------
# Invalid transaction state — REVERSED
# ---------------------------------------------------------------------------

class TestReversedTransactionIneligible:
    def test_reversed_raises_invalid_state(self, db_session: Session) -> None:
        customer = make_customer(db_session)
        txn = make_transaction(
            db_session, customer, reference="TXN-84724", status=TransactionStatus.REVERSED
        )

        with pytest.raises(AppError) as exc_info:
            _service(db_session).create_dispute(
                customer.reference, txn.reference, "Already reversed"
            )

        err = exc_info.value
        assert err.code == ErrorCode.INVALID_TRANSACTION_STATE
        assert "reversed" in err.message.lower()


# ---------------------------------------------------------------------------
# Duplicate open dispute
# ---------------------------------------------------------------------------

class TestDuplicateOpenDispute:
    def test_second_dispute_on_same_transaction_rejected(self, db_session: Session) -> None:
        customer = make_customer(db_session)
        txn = make_transaction(db_session, customer)
        case = make_support_case(db_session, customer, txn)
        make_dispute(db_session, case, txn, status=DisputeStatus.OPEN)

        with pytest.raises(AppError) as exc_info:
            _service(db_session).create_dispute(
                customer.reference, txn.reference, "Second attempt"
            )

        assert exc_info.value.code == ErrorCode.DISPUTE_NOT_ELIGIBLE

    def test_under_review_dispute_also_blocks(self, db_session: Session) -> None:
        customer = make_customer(db_session)
        txn = make_transaction(db_session, customer, reference="TXN-84725")
        case = make_support_case(db_session, customer, txn, reference="CASE-1002")
        make_dispute(
            db_session, case, txn, reference="DSP-1002", status=DisputeStatus.UNDER_REVIEW
        )

        with pytest.raises(AppError) as exc_info:
            _service(db_session).create_dispute(
                customer.reference, txn.reference, "Another attempt"
            )

        assert exc_info.value.code == ErrorCode.DISPUTE_NOT_ELIGIBLE


# ---------------------------------------------------------------------------
# Terminal dispute prevents redispute
# ---------------------------------------------------------------------------

class TestTerminalDisputePreventsRedispute:
    def test_resolved_dispute_blocks_new_dispute(self, db_session: Session) -> None:
        customer = make_customer(db_session)
        txn = make_transaction(db_session, customer)
        case = make_support_case(db_session, customer, txn)
        make_dispute(db_session, case, txn, status=DisputeStatus.RESOLVED)

        with pytest.raises(AppError) as exc_info:
            _service(db_session).create_dispute(
                customer.reference, txn.reference, "Trying again"
            )

        assert exc_info.value.code == ErrorCode.DISPUTE_NOT_ELIGIBLE

    def test_rejected_dispute_blocks_new_dispute(self, db_session: Session) -> None:
        customer = make_customer(db_session)
        txn = make_transaction(db_session, customer, reference="TXN-84726")
        case = make_support_case(db_session, customer, txn, reference="CASE-1003")
        make_dispute(
            db_session, case, txn, reference="DSP-1003", status=DisputeStatus.REJECTED
        )

        with pytest.raises(AppError) as exc_info:
            _service(db_session).create_dispute(
                customer.reference, txn.reference, "Trying again after rejection"
            )

        assert exc_info.value.code == ErrorCode.DISPUTE_NOT_ELIGIBLE
