"""API tests for POST /api/v1/support/messages -- the full AI-interprets ->
orchestration-coordinates -> backend-authorizes flow, end to end through the
real HTTP layer (against the in-memory SQLite test database)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.transaction.enums import TransactionStatus
from tests.conftest import make_customer, make_transaction

ENDPOINT = "/api/v1/support/messages"


class TestUnknownMessage:
    def test_unrelated_message_asks_for_more_information(
        self, client: TestClient, db_session: Session
    ) -> None:
        make_customer(db_session, reference="CUS-10001")

        response = client.post(
            ENDPOINT, json={"customer_reference": "CUS-10001", "message": "hello there"}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["outcome"] == "needs_info"
        assert body["intent"] == "unknown"
        assert body["transaction"] is None


class TestUnknownCustomer:
    def test_unknown_customer_is_a_404_not_a_200(self, client: TestClient) -> None:
        response = client.post(
            ENDPOINT, json={"customer_reference": "CUS-99999", "message": "help"}
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"


class TestTransactionStatus:
    def test_reports_status_of_own_transaction(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10001")
        make_transaction(
            db_session, customer, reference="TXN-84723", status=TransactionStatus.PENDING
        )

        response = client.post(
            ENDPOINT,
            json={
                "customer_reference": "CUS-10001",
                "message": "What is the status of TXN-84723?",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["outcome"] == "status_reported"
        assert body["transaction"]["reference"] == "TXN-84723"
        assert body["transaction"]["status"] == "PENDING"

    def test_other_customers_transaction_is_reported_as_not_found(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Cross-customer lookups must not leak whether the reference exists."""
        alice = make_customer(db_session, reference="CUS-10001")
        make_customer(db_session, reference="CUS-10021", name="Bob")
        make_transaction(db_session, alice, reference="TXN-84721")

        response = client.post(
            ENDPOINT,
            json={
                "customer_reference": "CUS-10021",
                "message": "check status of TXN-84721",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["outcome"] == "not_found"
        assert body["transaction"] is None


class TestDisputeViaMessage:
    def test_failed_transaction_creates_dispute(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10021")
        make_transaction(
            db_session, customer, reference="TXN-84722",
            status=TransactionStatus.FAILED, amount="800.00",
        )

        response = client.post(
            ENDPOINT,
            json={
                "customer_reference": "CUS-10021",
                "message": "I was charged 800 for TXN-84722 but it failed",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["outcome"] == "dispute_created"
        assert body["case_reference"].startswith("CASE-")
        assert body["dispute_reference"].startswith("DSP-")
        assert body["amount_mismatch"] is False

    def test_second_dispute_on_same_transaction_is_declined_not_errored(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10021")
        make_transaction(
            db_session, customer, reference="TXN-84722", status=TransactionStatus.FAILED
        )
        payload = {
            "customer_reference": "CUS-10021",
            "message": "I was charged for TXN-84722 but it failed",
        }

        first = client.post(ENDPOINT, json=payload)
        second = client.post(ENDPOINT, json=payload)

        assert first.json()["outcome"] == "dispute_created"
        assert second.status_code == 200
        assert second.json()["outcome"] == "dispute_declined"

    def test_pending_transaction_dispute_is_declined_not_errored(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10021")
        make_transaction(
            db_session, customer, reference="TXN-84723", status=TransactionStatus.PENDING
        )

        response = client.post(
            ENDPOINT,
            json={
                "customer_reference": "CUS-10021",
                "message": "I was charged for TXN-84723 but it failed",
            },
        )

        assert response.status_code == 200
        assert response.json()["outcome"] == "dispute_declined"

    def test_stated_amount_mismatch_is_flagged_but_backend_amount_wins(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10021")
        make_transaction(
            db_session, customer, reference="TXN-84722",
            status=TransactionStatus.FAILED, amount="800.00", currency="KES",
        )

        response = client.post(
            ENDPOINT,
            json={
                "customer_reference": "CUS-10021",
                "message": "I was charged KES 999999 for TXN-84722 but it failed",
            },
        )

        body = response.json()
        assert body["amount_mismatch"] is True
        # The reply and transaction summary use OUR amount, never the customer's.
        assert body["transaction"]["amount"] == "800.00"
        assert "999999" not in body["reply"]


class TestSupportCaseStatusViaMessage:
    def test_missing_case_reference_asks_for_it(
        self, client: TestClient, db_session: Session
    ) -> None:
        make_customer(db_session, reference="CUS-10021")

        response = client.post(
            ENDPOINT,
            json={"customer_reference": "CUS-10021", "message": "what's my case status"},
        )

        assert response.json()["outcome"] == "needs_info"

    def test_unknown_case_reference_is_not_found(
        self, client: TestClient, db_session: Session
    ) -> None:
        make_customer(db_session, reference="CUS-10021")

        response = client.post(
            ENDPOINT,
            json={"customer_reference": "CUS-10021", "message": "status of CASE-9999?"},
        )

        assert response.status_code == 200
        assert response.json()["outcome"] == "not_found"


class TestValidation:
    def test_blank_message_is_rejected(self, client: TestClient, db_session: Session) -> None:
        make_customer(db_session, reference="CUS-10021")

        response = client.post(
            ENDPOINT, json={"customer_reference": "CUS-10021", "message": ""}
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_missing_fields_use_the_standard_error_envelope(self, client: TestClient) -> None:
        response = client.post(ENDPOINT, json={})

        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "customer_reference" in body["error"]["message"]
