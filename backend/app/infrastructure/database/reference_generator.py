"""Concurrency-safe reference generator.

Produces human-friendly references (e.g. ``CUS-10001``, ``TXN-84721``)
by drawing from a database sequence in PostgreSQL, or from a
thread-safe in-process counter when running against SQLite (test
environment).

Design rationale — see ADR-004:
  - PostgreSQL sequences are atomic and non-blocking across concurrent
    transactions.  nextval() never returns the same value twice, even
    if the transaction that consumed the value is later rolled back.
  - SQLite does not support standalone sequences.  The fallback counter
    is thread-safe within a single-process run and adequate for tests.
"""

import threading
from collections.abc import Iterator
from itertools import count

from sqlalchemy import text
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Sequence names — one per entity type, matching the names created in
# migration 001_create_domain_tables.
# ---------------------------------------------------------------------------
_CUSTOMER_SEQ = "customer_ref_seq"
_TRANSACTION_SEQ = "transaction_ref_seq"
_SUPPORT_CASE_SEQ = "support_case_ref_seq"
_DISPUTE_SEQ = "dispute_ref_seq"


# ---------------------------------------------------------------------------
# SQLite fallback — in-process thread-safe counter
# ---------------------------------------------------------------------------
_lock = threading.Lock()
_sqlite_counters: dict[str, Iterator[int]] = {
    _CUSTOMER_SEQ: count(10001),
    _TRANSACTION_SEQ: count(80001),
    _SUPPORT_CASE_SEQ: count(1001),
    _DISPUTE_SEQ: count(1001),
}


def _next_value(session: Session, sequence_name: str) -> int:
    """Return the next integer from the named sequence.

    Uses ``nextval()`` in PostgreSQL, or advances the in-process counter
    for SQLite.  Both are safe under concurrent access within their
    respective environments.
    """
    dialect = session.bind.dialect.name if session.bind else "sqlite"  # type: ignore[union-attr]
    if dialect == "postgresql":
        row = session.execute(text(f"SELECT nextval('{sequence_name}')")).one()
        return int(row[0])
    # SQLite fallback
    with _lock:
        return next(_sqlite_counters[sequence_name])


def next_customer_reference(session: Session) -> str:
    """Return the next ``CUS-{n:05d}`` reference."""
    n = _next_value(session, _CUSTOMER_SEQ)
    return f"CUS-{n:05d}"


def next_transaction_reference(session: Session) -> str:
    """Return the next ``TXN-{n:05d}`` reference."""
    n = _next_value(session, _TRANSACTION_SEQ)
    return f"TXN-{n:05d}"


def next_support_case_reference(session: Session) -> str:
    """Return the next ``CASE-{n:04d}`` reference."""
    n = _next_value(session, _SUPPORT_CASE_SEQ)
    return f"CASE-{n:04d}"


def next_dispute_reference(session: Session) -> str:
    """Return the next ``DSP-{n:04d}`` reference."""
    n = _next_value(session, _DISPUTE_SEQ)
    return f"DSP-{n:04d}"
