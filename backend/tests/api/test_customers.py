"""API tests for GET /api/v1/customers/{reference}."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import make_customer


class TestGetCustomer:
    def test_returns_customer_for_valid_reference(
        self, client: TestClient, db_session: Session
    ) -> None:
        make_customer(
            db_session,
            reference="CUS-10021",
            name="Bob Omondi",
            phone="+254700000021",
            email="bob@example.com",
        )

        response = client.get("/api/v1/customers/CUS-10021")

        assert response.status_code == 200
        data = response.json()
        assert data["reference"] == "CUS-10021"
        assert data["name"] == "Bob Omondi"
        # Contact details are masked: there is no authentication yet, so the
        # API must never return a customer's full phone/email to any caller.
        assert data["phone"] == "+254*******21"
        assert data["email"] == "b**@example.com"
        assert "0700000021" not in response.text
        assert "bob@example.com" not in response.text
        # Internal UUID must never appear in the response
        assert "id" not in data

    def test_returns_404_for_unknown_reference(
        self, client: TestClient, db_session: Session
    ) -> None:
        response = client.get("/api/v1/customers/CUS-99999")

        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "CUSTOMER_NOT_FOUND"
