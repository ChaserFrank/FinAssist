"""Seed synthetic customer and transaction data for local development."""

from decimal import Decimal

from app.domain.customer import Customer
from app.domain.transaction.models import Transaction
from app.infrastructure.database.session import SessionLocal

DEMO_CUSTOMERS = [
    {
        "reference": "CUS-DEMO-001",
        "name": "Amina Otieno",
        "phone": "+254700000001",
        "email": "amina.otieno@example.com",
    },
    {
        "reference": "CUS-DEMO-002",
        "name": "Brian Kamau",
        "phone": "+254700000002",
        "email": "brian.kamau@example.com",
    },
    {
        "reference": "CUS-DEMO-003",
        "name": "Carol Wanjiku",
        "phone": "+254700000003",
        "email": "carol.wanjiku@example.com",
    },
    {
        "reference": "CUS-DEMO-004",
        "name": "David Mwangi",
        "phone": "+254700000004",
        "email": "david.mwangi@example.com",
    },
]

DEMO_TRANSACTIONS = [
    {
        "reference": "TXN-DEMO-001",
        "customer_id": "CUS-DEMO-001",
        "amount": Decimal("3500.00"),
        "currency": "KES",
        "status": "PENDING",
        "payment_method": "Mobile Money",
        "description": "Payment processing",
    },
    {
        "reference": "TXN-DEMO-002",
        "customer_id": "CUS-DEMO-002",
        "amount": Decimal("1250.00"),
        "currency": "KES",
        "status": "SUCCESS",
        "payment_method": "Mobile Money",
        "description": "Payment completed successfully",
    },
    {
        "reference": "TXN-DEMO-003",
        "customer_id": "CUS-DEMO-003",
        "amount": Decimal("2800.00"),
        "currency": "KES",
        "status": "FAILED",
        "payment_method": "Card",
        "description": "Payment could not be completed",
    },
    {
        "reference": "TXN-DEMO-004",
        "customer_id": "CUS-DEMO-004",
        "amount": Decimal("5000.00"),
        "currency": "KES",
        "status": "REVERSED",
        "payment_method": "Mobile Money",
        "description": "Payment was reversed",
    },
]


def main() -> None:
    with SessionLocal() as session:
        for data in DEMO_CUSTOMERS:
            existing = (
                session.query(Customer)
                .filter(Customer.reference == data["reference"])
                .first()
            )

            if existing:
                continue

            session.add(Customer(**data))

        session.flush()

        for data in DEMO_TRANSACTIONS:
            existing = (
                session.query(Transaction)
                .filter(Transaction.reference == data["reference"])
                .first()
            )

            if existing:
                continue

            session.add(Transaction(**data))

        session.commit()

    print(
        f"Seeded {len(DEMO_CUSTOMERS)} synthetic customers and "
        f"{len(DEMO_TRANSACTIONS)} synthetic transaction scenarios."
    )


if __name__ == "__main__":
    main()