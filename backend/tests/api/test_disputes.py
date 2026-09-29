"""API tests for dispute endpoints.

POST /api/v1/disputes
GET  /api/v1/disputes/{reference}

Tests cover the full documented API contract and all error codes
in the eligibility pipeline.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.dispute.enums import DisputeStatus
from app.domain.transaction.enums import TransactionStatus
from tests.conftest import (
    make_customer,
    make_dispute,
    make_support_case,
    make_transaction,
)


def _dispute_payload(
    customer_reference: str = "CUS-10021",
    transaction_reference: str = "TXN-84721",
    reason: str = "Payment failed but account was charged",
) -> dict:
    return {
        "customer_reference": customer_reference,
        "transaction_reference": transaction_reference,
        "reason": reason,
    }


class TestCreateDispute:
    def test_creates_dispute_for_failed_transaction(
        self, client: TestClient, db_session: Session
    ) -> None:
        """The primary FinAssist scenario: charged despite payment failure."""
        customer = make_customer(db_session, reference="CUS-10021")
        make_transaction(
            db_session, customer,
            reference="TXN-84721",
            status=TransactionStatus.FAILED,
        )

        response = client.post("/api/v1/disputes", json=_dispute_payload())

        assert response.status_code == 201
        data = response.json()
        assert data["reference"].startswith("DSP-")
        assert data["support_case_reference"].startswith("CASE-")
        assert data["transaction_reference"] == "TXN-84721"
        assert data["status"] == "OPEN"

    def test_creates_dispute_for_success_transaction(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10021")
        make_transaction(
            db_session, customer,
            reference="TXN-84721",
            status=TransactionStatus.SUCCESS,
        )

        response = client.post(
            "/api/v1/disputes",
            json=_dispute_payload(reason="Unauthorised charge"),
        )

        assert response.status_code == 201

    def test_response_contains_both_references(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10021")
        make_transaction(
            db_session, customer,
            reference="TXN-84721",
            status=TransactionStatus.SUCCESS,
        )

        data = client.post("/api/v1/disputes", json=_dispute_payload()).json()

        # Both the dispute reference and the support case reference must be present
        assert "reference" in data
        assert "support_case_reference" in data
        assert data["reference"] != data["support_case_reference"]

    def test_returns_404_when_transaction_not_found(
        self, client: TestClient, db_session: Session
    ) -> None:
        make_customer(db_session, reference="CUS-10021")

        response = client.post(
            "/api/v1/disputes",
            json=_dispute_payload(transaction_reference="TXN-99999"),
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "TRANSACTION_NOT_FOUND"

    def test_returns_404_when_customer_not_found(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10021")
        make_transaction(db_session, customer, reference="TXN-84721")

        response = client.post(
            "/api/v1/disputes",
            json=_dispute_payload(customer_reference="CUS-99999"),
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"

    def test_returns_400_for_customer_transaction_mismatch(
        self, client: TestClient, db_session: Session
    ) -> None:
        alice = make_customer(db_session, reference="CUS-10001")
        make_customer(db_session, reference="CUS-10021", name="Bob")
        make_transaction(db_session, alice, reference="TXN-84721")

        response = client.post(
            "/api/v1/disputes",
            json=_dispute_payload(customer_reference="CUS-10021"),
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "CUSTOMER_TRANSACTION_MISMATCH"

    def test_returns_422_for_pending_transaction(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10021")
        make_transaction(
            db_session, customer,
            reference="TXN-84721",
            status=TransactionStatus.PENDING,
        )

        response = client.post("/api/v1/disputes", json=_dispute_payload())

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_TRANSACTION_STATE"

    def test_returns_422_for_reversed_transaction(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10021")
        make_transaction(
            db_session, customer,
            reference="TXN-84721",
            status=TransactionStatus.REVERSED,
        )

        response = client.post("/api/v1/disputes", json=_dispute_payload())

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_TRANSACTION_STATE"

    def test_returns_409_for_duplicate_open_dispute(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10021")
        txn = make_transaction(
            db_session, customer,
            reference="TXN-84721",
            status=TransactionStatus.SUCCESS,
        )
        case = make_support_case(db_session, customer, txn)
        make_dispute(db_session, case, txn, status=DisputeStatus.OPEN)

        response = client.post("/api/v1/disputes", json=_dispute_payload())

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "DISPUTE_NOT_ELIGIBLE"

    def test_error_envelope_shape(
        self, client: TestClient, db_session: Session
    ) -> None:
        """All error responses must conform to the documented envelope."""
        response = client.post(
            "/api/v1/disputes",
            json=_dispute_payload(transaction_reference="TXN-99999"),
        )

        body = response.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
        # The API must never leak raw exception details
        assert "traceback" not in str(body).lower()


class TestGetDispute:
    def test_returns_404_for_unknown_reference(
        self, client: TestClient, db_session: Session
    ) -> None:
        make_customer(db_session)  # ensure DB is populated

        response = client.get("/api/v1/disputes/DSP-9999")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "DISPUTE_NOT_FOUND"
