"""create support cases table.

Revision ID: 526cf63d194d
Revises: a18fc526a575
Create Date: 2026-09-28 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "526cf63d194d"
down_revision: str | None = "a18fc526a575"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.create_table(
        "support_cases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=False),
        sa.Column("transaction_reference", sa.String(length=100), nullable=False),
        sa.Column("customer_id", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_support_cases_customer_id"),
        "support_cases",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_support_cases_reference"),
        "support_cases",
        ["reference"],
        unique=True,
    )
    op.create_index(
        op.f("ix_support_cases_transaction_reference"),
        "support_cases",
        ["transaction_reference"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(
        op.f("ix_support_cases_transaction_reference"),
        table_name="support_cases",
    )
    op.drop_index(
        op.f("ix_support_cases_reference"),
        table_name="support_cases",
    )
    op.drop_index(
        op.f("ix_support_cases_customer_id"),
        table_name="support_cases",
    )
    op.drop_table("support_cases")