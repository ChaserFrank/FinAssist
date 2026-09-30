"""Enforce status enums at the database level.

Revision ID: 002
Revises: 001
Create Date: 2026-09-28

The project convention is "enums, not free-text strings" for every status
column, but migration 001 stored them as bare VARCHAR(16), so the database
would happily accept ``status = 'banana'``. This adds a CHECK constraint per
table, mirroring ``TransactionStatus`` / ``SupportCaseStatus`` /
``DisputeStatus``. The values below are deliberately literal (a migration is
a frozen snapshot and must not import application enums that may change).

PostgreSQL only: SQLite cannot ``ALTER TABLE ... ADD CONSTRAINT``, and SQLite
is used solely for the unit-test database, which is built from the ORM
metadata (whose models declare the same constraints) rather than from
migrations.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CHECKS: dict[str, tuple[str, ...]] = {
    "transactions": ("PENDING", "SUCCESS", "FAILED", "REVERSED"),
    "support_cases": ("OPEN", "IN_REVIEW", "RESOLVED", "CLOSED"),
    "disputes": ("OPEN", "UNDER_REVIEW", "RESOLVED", "REJECTED"),
}


def _is_postgresql() -> bool:
    bind = op.get_context().bind
    return bind is not None and bind.dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgresql():
        return
    for table, values in _CHECKS.items():
        allowed = ", ".join(f"'{v}'" for v in values)
        op.create_check_constraint(f"ck_{table}_status", table, f"status IN ({allowed})")


def downgrade() -> None:
    if not _is_postgresql():
        return
    for table in _CHECKS:
        op.drop_constraint(f"ck_{table}_status", table, type_="check")
