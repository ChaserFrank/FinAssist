"""Database-level guarantees that SQLite cannot prove. Run against real PostgreSQL.

Locally:   TEST_DATABASE_URL=<url of a database named *_test> pytest tests/integration
CI:        a throwaway Postgres is started and REQUIRE_INTEGRATION=1 is set.
"""

import threading
import uuid
from decimal import Decimal

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.application.dispute_service import DisputeService
from app.core.exceptions import AppError, ErrorCode
from app.domain.customer.models import Customer
from app.domain.dispute.models import Dispute
from app.domain.support.models import SupportCase
from app.domain.transaction.enums import TransactionStatus
from app.domain.transaction.models import Transaction
from app.infrastructure.database.base import Base
from app.infrastructure.database.reference_generator import (
    next_dispute_reference,
    next_support_case_reference,
)
from app.infrastructure.repositories.dispute_repo import DisputeRepository

pytestmark = pytest.mark.integration


def _seed(engine: Engine, status: TransactionStatus = TransactionStatus.SUCCESS):
    """Commit a customer + transaction (visible to other connections)."""
    tag = uuid.uuid4().hex[:8]
    with sessionmaker(bind=engine, expire_on_commit=False)() as s:
        customer = Customer(
            id=uuid.uuid4(), reference=f"CUS-T{tag}", name="Integration Test",
            phone="+254700000000", email="it@example.com",
        )
        s.add(customer)
        s.flush()
        txn = Transaction(
            id=uuid.uuid4(), reference=f"TXN-T{tag}", customer_id=customer.id,
            amount=Decimal("1000.00"), currency="KES", status=status, payment_method="test",
        )
        s.add(txn)
        s.commit()
        return customer.reference, txn.reference, customer.id, txn.id


def _cleanup(engine: Engine, customer_id: uuid.UUID, txn_id: uuid.UUID) -> None:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM disputes WHERE transaction_id = :t"), {"t": txn_id})
        conn.execute(text("DELETE FROM support_cases WHERE customer_id = :c"), {"c": customer_id})
        conn.execute(text("DELETE FROM transactions WHERE id = :t"), {"t": txn_id})
        conn.execute(text("DELETE FROM customers WHERE id = :c"), {"c": customer_id})


def _count(engine: Engine, model, **filters) -> int:
    with sessionmaker(bind=engine)() as s:
        stmt = select(func.count()).select_from(model)
        for column, value in filters.items():
            stmt = stmt.where(getattr(model, column) == value)
        return s.scalar(stmt)


class TestConcurrency:
    def test_concurrent_disputes_exactly_one_wins(self, pg_engine: Engine) -> None:
        """N simultaneous requests for one transaction -> exactly one dispute + case."""
        cust_ref, txn_ref, cust_id, txn_id = _seed(pg_engine)
        workers = 8
        barrier = threading.Barrier(workers)
        results: list[str] = []
        lock = threading.Lock()

        def worker() -> None:
            with sessionmaker(bind=pg_engine, expire_on_commit=False)() as session:
                service = DisputeService(session)
                barrier.wait(timeout=10)  # release all threads at once
                try:
                    service.create_dispute(cust_ref, txn_ref, "concurrent attempt")
                    outcome = "created"
                except AppError as exc:
                    outcome = str(exc.code)
                with lock:
                    results.append(outcome)

        try:
            threads = [threading.Thread(target=worker) for _ in range(workers)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)

            assert results.count("created") == 1, results
            assert results.count(str(ErrorCode.DISPUTE_NOT_ELIGIBLE)) == workers - 1, results
            assert _count(pg_engine, Dispute, transaction_id=txn_id) == 1
            # Losers rolled back completely: no orphan support cases.
            assert _count(pg_engine, SupportCase, transaction_id=txn_id) == 1
        finally:
            _cleanup(pg_engine, cust_id, txn_id)

    def test_partial_unique_index_is_a_real_backstop(
        self, pg_engine: Engine, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Even with the application-level check disabled, the DB refuses a 2nd active dispute."""
        cust_ref, txn_ref, cust_id, txn_id = _seed(pg_engine)
        try:
            with sessionmaker(bind=pg_engine, expire_on_commit=False)() as session:
                DisputeService(session).create_dispute(cust_ref, txn_ref, "first")

            monkeypatch.setattr(
                DisputeRepository, "find_active_by_transaction_id", lambda self, tid: None
            )
            with sessionmaker(bind=pg_engine, expire_on_commit=False)() as session:
                with pytest.raises(AppError) as exc:
                    DisputeService(session).create_dispute(cust_ref, txn_ref, "second")
                assert exc.value.code == ErrorCode.DISPUTE_NOT_ELIGIBLE
                # Session is clean and reusable after the rollback.
                assert session.scalar(select(func.count()).select_from(Dispute)) >= 1

            assert _count(pg_engine, Dispute, transaction_id=txn_id) == 1
            assert _count(pg_engine, SupportCase, transaction_id=txn_id) == 1
        finally:
            _cleanup(pg_engine, cust_id, txn_id)


class TestSchema:
    def test_check_constraint_rejects_invalid_status(self, pg_engine: Engine) -> None:
        cust_ref, _txn_ref, cust_id, txn_id = _seed(pg_engine)
        try:
            with pytest.raises(IntegrityError), pg_engine.begin() as conn:
                conn.execute(
                    text("UPDATE transactions SET status = 'BANANA' WHERE id = :t"),
                    {"t": txn_id},
                )
        finally:
            _cleanup(pg_engine, cust_id, txn_id)

    def test_migrated_schema_matches_orm_models(self, pg_engine: Engine) -> None:
        """No column/table drift between migrations and models (index cosmetics ignored)."""
        with pg_engine.connect() as conn:
            diffs = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        structural = [
            d for d in diffs
            if d[0] in {"add_table", "remove_table", "add_column", "remove_column", "modify_type"}
        ]
        assert structural == []

    def test_resolved_dispute_does_not_block_index_but_active_does(
        self, pg_engine: Engine
    ) -> None:
        """Partial index semantics: many closed disputes OK, two active ones not."""
        cust_ref, txn_ref, cust_id, txn_id = _seed(pg_engine)
        try:
            with sessionmaker(bind=pg_engine, expire_on_commit=False)() as s:
                case = SupportCase(
                    id=uuid.uuid4(), reference=f"CASE-T{uuid.uuid4().hex[:8]}",
                    customer_id=cust_id, transaction_id=txn_id, category="t",
                    description="d", status="OPEN",
                )
                s.add(case)
                s.flush()

                def add(status: str) -> None:
                    s.add(Dispute(
                        id=uuid.uuid4(), reference=f"DSP-T{uuid.uuid4().hex[:8]}",
                        support_case_id=case.id, transaction_id=txn_id,
                        reason="r", status=status,
                    ))
                    s.flush()

                add("RESOLVED")
                add("REJECTED")
                add("OPEN")
                with pytest.raises(IntegrityError):
                    add("UNDER_REVIEW")
                s.rollback()
        finally:
            _cleanup(pg_engine, cust_id, txn_id)


class TestReferenceSequences:
    def test_sequences_are_strictly_increasing_across_sessions(self, pg_engine: Engine) -> None:
        seen: list[str] = []
        for _ in range(5):
            with sessionmaker(bind=pg_engine)() as s:
                seen.append(next_support_case_reference(s))
        numbers = [int(ref.split("-")[1]) for ref in seen]
        assert numbers == sorted(set(numbers))

    def test_sequence_values_are_never_reused_after_rollback(self, pg_engine: Engine) -> None:
        with sessionmaker(bind=pg_engine)() as s:
            burned = next_dispute_reference(s)
            s.rollback()  # the transaction that "used" it never commits
        with sessionmaker(bind=pg_engine)() as s:
            following = next_dispute_reference(s)
        assert int(following.split("-")[1]) > int(burned.split("-")[1])

    def test_concurrent_reference_generation_yields_unique_values(
        self, pg_engine: Engine
    ) -> None:
        results: list[str] = []
        lock = threading.Lock()

        def worker() -> None:
            with sessionmaker(bind=pg_engine)() as s:
                ref = next_support_case_reference(s)
            with lock:
                results.append(ref)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        assert len(results) == 20
        assert len(set(results)) == 20


def test_session_helper_type(pg_session: Session) -> None:
    """Sanity: the shared fixture yields a usable session."""
    assert pg_session.scalar(text("SELECT 1")) == 1
