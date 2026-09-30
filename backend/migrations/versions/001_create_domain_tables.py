"""Create domain tables: customers, transactions, support_cases, disputes.

Revision ID: 001
Revises: None
Create Date: 2026-09-27

This migration creates all four core domain tables.  In PostgreSQL, it
also creates one database sequence per entity type for concurrency-safe
reference generation (see docs/decisions/004-reference-generation-and-
dispute-integrity.md).  The sequence creation steps are guarded with
dialect checks so the same migration runs without error on SQLite (used
in the test environment).

A partial unique index on disputes(transaction_id) prevents more than one
active (OPEN or UNDER_REVIEW) dispute per transaction — enforced at the
database level as a second line of defence after the application-level
check in DisputeService.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _is_postgresql() -> bool:
    bind = op.get_context().bind
    return bind is not None and bind.dialect.name == "postgresql"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # PostgreSQL sequences for concurrency-safe reference generation.
    # Each sequence starts at a value that matches the demo-data seed
    # ranges defined in docs/database.md.
    # ------------------------------------------------------------------
    if _is_postgresql():
        op.execute("CREATE SEQUENCE IF NOT EXISTS customer_ref_seq START WITH 10001 INCREMENT BY 1")
        op.execute(
            "CREATE SEQUENCE IF NOT EXISTS transaction_ref_seq START WITH 80001 INCREMENT BY 1"
        )
        op.execute(
            "CREATE SEQUENCE IF NOT EXISTS support_case_ref_seq START WITH 1001 INCREMENT BY 1"
        )
        op.execute(
            "CREATE SEQUENCE IF NOT EXISTS dispute_ref_seq START WITH 1001 INCREMENT BY 1"
        )

    # ------------------------------------------------------------------
    # customers
    # ------------------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reference", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference", name="uq_customers_reference"),
    )
    op.create_index("ix_customers_reference", "customers", ["reference"])

    # ------------------------------------------------------------------
    # transactions
    # ------------------------------------------------------------------
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reference", sa.String(32), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("payment_method", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference", name="uq_transactions_reference"),
    )
    op.create_index("ix_transactions_reference", "transactions", ["reference"])
    op.create_index("ix_transactions_customer_id", "transactions", ["customer_id"])

    # ------------------------------------------------------------------
    # support_cases
    # ------------------------------------------------------------------
    op.create_table(
        "support_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reference", sa.String(32), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=True),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["transaction_id"], ["transactions.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference", name="uq_support_cases_reference"),
    )
    op.create_index("ix_support_cases_reference", "support_cases", ["reference"])
    op.create_index("ix_support_cases_customer_id", "support_cases", ["customer_id"])
    op.create_index("ix_support_cases_transaction_id", "support_cases", ["transaction_id"])

    # ------------------------------------------------------------------
    # disputes
    # ------------------------------------------------------------------
    op.create_table(
        "disputes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reference", sa.String(32), nullable=False),
        sa.Column("support_case_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["support_case_id"], ["support_cases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference", name="uq_disputes_reference"),
    )
    op.create_index("ix_disputes_reference", "disputes", ["reference"])
    op.create_index("ix_disputes_support_case_id", "disputes", ["support_case_id"])
    op.create_index("ix_disputes_transaction_id", "disputes", ["transaction_id"])

    # Partial unique index: at most one OPEN or UNDER_REVIEW dispute per
    # transaction.  Supported by PostgreSQL and SQLite >= 3.8.0.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_disputes_open_per_transaction
            ON disputes (transaction_id)
            WHERE status IN ('OPEN', 'UNDER_REVIEW')
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_disputes_open_per_transaction")
    op.drop_table("disputes")
    op.drop_table("support_cases")
    op.drop_table("transactions")
    op.drop_table("customers")

    if _is_postgresql():
        op.execute("DROP SEQUENCE IF EXISTS dispute_ref_seq")
        op.execute("DROP SEQUENCE IF EXISTS support_case_ref_seq")
        op.execute("DROP SEQUENCE IF EXISTS transaction_ref_seq")
        op.execute("DROP SEQUENCE IF EXISTS customer_ref_seq")
