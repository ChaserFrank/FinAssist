"""Seed synthetic demo data for local development and demos.

Creates reproducible, named records that match the examples used in
documentation (docs/api.md, docs/database.md) and tests.  Run once
after applying migrations:

    docker compose exec backend python -m scripts.seed_demo_data

Idempotent: skips records whose reference already exists, so re-running
is safe.  No real customer or financial data is ever used here.

Customers:
  CUS-10001  Alice Kamau
  CUS-10021  Bob Omondi

Transactions (covering all four statuses):
  TXN-84721  CUS-10021  3500.00 KES  SUCCESS   (disputable)
  TXN-84722  CUS-10021   800.00 KES  FAILED    (disputable — charged but failed)
  TXN-84723  CUS-10001  1200.00 KES  PENDING   (not yet settled)
  TXN-84724  CUS-10001  2000.00 KES  REVERSED  (funds returned)
  TXN-84725  CUS-10001   500.00 KES  SUCCESS   (disputable)
"""

import sys
import uuid
from decimal import Decimal

# Allow running as  python -m scripts.seed_demo_data  from the backend/ dir.
sys.path.insert(0, ".")

from sqlalchemy import select

from app.domain.customer.models import Customer
from app.domain.transaction.enums import TransactionStatus
from app.domain.transaction.models import Transaction
from app.infrastructure.database.session import SessionLocal

# ---------------------------------------------------------------------------
# Seed fixtures
# ---------------------------------------------------------------------------

_CUSTOMERS = [
    {
        "reference": "CUS-10001",
        "name": "Alice Kamau",
        "phone": "+254700000001",
        "email": "alice@example.com",
    },
    {
        "reference": "CUS-10021",
        "name": "Bob Omondi",
        "phone": "+254700000021",
        "email": "bob@example.com",
    },
]

_TRANSACTIONS = [
    # reference       customer_ref   amount    currency  status                      method
    ("TXN-84721", "CUS-10021", "3500.00", "KES", TransactionStatus.SUCCESS, "M-Pesa"),
    ("TXN-84722", "CUS-10021", "800.00", "KES", TransactionStatus.FAILED, "M-Pesa"),
    ("TXN-84723", "CUS-10001", "1200.00", "KES", TransactionStatus.PENDING, "card"),
    ("TXN-84724", "CUS-10001", "2000.00", "KES", TransactionStatus.REVERSED, "card"),
    ("TXN-84725", "CUS-10001", "500.00", "KES", TransactionStatus.SUCCESS, "M-Pesa"),
]


def _upsert_customers(session) -> dict[str, uuid.UUID]:
    """Insert customers that don't already exist. Returns ref → id map."""
    ref_to_id: dict[str, uuid.UUID] = {}
    for c in _CUSTOMERS:
        existing = session.scalars(
            select(Customer).where(Customer.reference == c["reference"])
        ).first()
        if existing:
            print(f"  skip {c['reference']} (already exists)")
            ref_to_id[c["reference"]] = existing.id
        else:
            obj = Customer(id=uuid.uuid4(), **c)
            session.add(obj)
            session.flush()
            ref_to_id[c["reference"]] = obj.id
            print(f"  created {c['reference']}  {c['name']}")
    return ref_to_id


def _upsert_transactions(session, customer_ids: dict[str, uuid.UUID]) -> None:
    """Insert transactions that don't already exist."""
    for ref, cust_ref, amount, currency, status, method in _TRANSACTIONS:
        existing = session.scalars(
            select(Transaction).where(Transaction.reference == ref)
        ).first()
        if existing:
            print(f"  skip {ref} (already exists)")
            continue
        txn = Transaction(
            id=uuid.uuid4(),
            reference=ref,
            customer_id=customer_ids[cust_ref],
            amount=Decimal(amount),
            currency=currency,
            status=status,
            payment_method=method,
        )
        session.add(txn)
        session.flush()
        print(f"  created {ref}  {amount} {currency}  {status}")


def main() -> None:
    print("Seeding demo data...")
    session = SessionLocal()
    try:
        with session.begin():
            customer_ids = _upsert_customers(session)
            _upsert_transactions(session, customer_ids)
        print("Done.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
