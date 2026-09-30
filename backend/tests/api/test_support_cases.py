"""API tests for support case endpoints.

POST /api/v1/support/cases
GET  /api/v1/support/cases/{reference}
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.transaction.enums import TransactionStatus
from tests.conftest import make_customer, make_transaction


class TestCreateSupportCase:
    def test_creates_case_without_transaction(
        self, client: TestClient, db_session: Session
    ) -> None:
        make_customer(db_session, reference="CUS-10001")

        response = client.post(
            "/api/v1/support/cases",
            json={
                "customer_reference": "CUS-10001",
                "category": "general_inquiry",
                "description": "I have a question about my account.",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["reference"].startswith("CASE-")
        assert data["customer_reference"] == "CUS-10001"
        assert data["transaction_reference"] is None
        assert data["status"] == "OPEN"

    def test_creates_case_with_transaction(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session, reference="CUS-10021")
        make_transaction(
            db_session, customer,
            reference="TXN-84721",
            status=TransactionStatus.SUCCESS,
        )

        response = client.post(
            "/api/v1/support/cases",
            json={
                "customer_reference": "CUS-10021",
                "transaction_reference": "TXN-84721",
                "category": "payment_dispute",
                "description": "I was charged but did not receive the service.",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["transaction_reference"] == "TXN-84721"

    def test_returns_404_for_unknown_customer(
        self, client: TestClient, db_session: Session
    ) -> None:
        response = client.post(
            "/api/v1/support/cases",
            json={
                "customer_reference": "CUS-99999",
                "category": "general_inquiry",
                "description": "Test.",
            },
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"

    def test_returns_400_for_customer_transaction_mismatch(
        self, client: TestClient, db_session: Session
    ) -> None:
        alice = make_customer(db_session, reference="CUS-10001")
        make_customer(db_session, reference="CUS-10002", name="Bob")
        make_transaction(db_session, alice, reference="TXN-84721")

        # Bob tries to open a case about Alice's transaction
        response = client.post(
            "/api/v1/support/cases",
            json={
                "customer_reference": "CUS-10002",
                "transaction_reference": "TXN-84721",
                "category": "payment_dispute",
                "description": "Not my transaction.",
            },
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "CUSTOMER_TRANSACTION_MISMATCH"


class TestGetSupportCase:
    def test_returns_404_for_unknown_reference(
        self, client: TestClient, db_session: Session
    ) -> None:
        response = client.get("/api/v1/support/cases/CASE-9999")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "SUPPORT_CASE_NOT_FOUND"
