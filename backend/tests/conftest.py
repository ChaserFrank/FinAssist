"""Shared test fixtures.

Uses an in-memory SQLite database — no running Postgres required for unit
and API tests.  Tests that require PostgreSQL-specific behaviour (e.g.
partial index concurrency) are in tests/integration/ and are decorated
with @pytest.mark.integration.

The ``db_session`` fixture yields a session whose changes are rolled back
after each test, so tests are isolated and ordering-independent.
"""

import uuid
from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.domain.customer.models import Customer
from app.domain.dispute.enums import DisputeStatus
from app.domain.dispute.models import Dispute
from app.domain.support.enums import SupportCaseStatus
from app.domain.support.models import SupportCase
from app.domain.transaction.enums import TransactionStatus
from app.domain.transaction.models import Transaction
from app.infrastructure.database.base import Base
from app.main import app


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Yield a fresh in-memory database session for each test."""
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """Return a FastAPI TestClient wired to the test database session."""

    def _override_get_db():
        yield db_session

    from app.api.dependencies import get_db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Common domain object factories
# ---------------------------------------------------------------------------

def make_customer(
    session: Session,
    *,
    reference: str = "CUS-10001",
    name: str = "Alice Kamau",
    phone: str = "+254700000001",
    email: str = "alice@example.com",
) -> Customer:
    c = Customer(id=uuid.uuid4(), reference=reference, name=name, phone=phone, email=email)
    session.add(c)
    session.commit()
    return c


def make_transaction(
    session: Session,
    customer: Customer,
    *,
    reference: str = "TXN-84721",
    amount: Decimal = Decimal("3500.00"),
    currency: str = "KES",
    status: TransactionStatus = TransactionStatus.SUCCESS,
    payment_method: str = "M-Pesa",
) -> Transaction:
    t = Transaction(
        id=uuid.uuid4(),
        reference=reference,
        customer_id=customer.id,
        amount=amount,
        currency=currency,
        status=status,
        payment_method=payment_method,
    )
    session.add(t)
    session.commit()
    return t


def make_support_case(
    session: Session,
    customer: Customer,
    transaction: Transaction | None = None,
    *,
    reference: str = "CASE-1001",
    category: str = "payment_dispute",
    description: str = "Test case",
    status: SupportCaseStatus = SupportCaseStatus.OPEN,
) -> SupportCase:
    sc = SupportCase(
        id=uuid.uuid4(),
        reference=reference,
        customer_id=customer.id,
        transaction_id=transaction.id if transaction else None,
        category=category,
        description=description,
        status=status,
    )
    session.add(sc)
    session.commit()
    return sc


def make_dispute(
    session: Session,
    support_case: SupportCase,
    transaction: Transaction,
    *,
    reference: str = "DSP-1001",
    reason: str = "Payment failed but charged",
    status: DisputeStatus = DisputeStatus.OPEN,
) -> Dispute:
    d = Dispute(
        id=uuid.uuid4(),
        reference=reference,
        support_case_id=support_case.id,
        transaction_id=transaction.id,
        reason=reason,
        status=status,
    )
    session.add(d)
    session.commit()
    return d
