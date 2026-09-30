"""API tests for GET /api/v1/transactions/{reference}."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.transaction.enums import TransactionStatus
from tests.conftest import make_customer, make_transaction


class TestGetTransaction:
    def test_returns_transaction_for_valid_reference(
        self, client: TestClient, db_session: Session
    ) -> None:
        customer = make_customer(db_session)
        make_transaction(
            db_session, customer,
            reference="TXN-84721",
            amount=Decimal("3500.00"),
            currency="KES",
            status=TransactionStatus.SUCCESS,
        )

        response = client.get("/api/v1/transactions/TXN-84721")

        assert response.status_code == 200
        data = response.json()
        assert data["reference"] == "TXN-84721"
        assert data["customer_reference"] == customer.reference
        assert data["currency"] == "KES"
        assert data["status"] == "SUCCESS"
        assert data["payment_method"] == "M-Pesa"

    def test_returns_404_for_unknown_reference(
        self, client: TestClient, db_session: Session
    ) -> None:
        response = client.get("/api/v1/transactions/TXN-99999")

        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "TRANSACTION_NOT_FOUND"
        assert "TXN-99999" in body["error"]["message"]
