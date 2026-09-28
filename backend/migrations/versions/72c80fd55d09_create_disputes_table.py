"""create disputes table

Revision ID: 72c80fd55d09
Revises: 579d3effeeeb
Create Date: 2026-09-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "72c80fd55d09"
down_revision: str | None = "579d3effeeeb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "disputes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=False),
        sa.Column(
            "support_case_reference",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "transaction_reference",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference"),
    )

    op.create_index(
        "ix_disputes_reference",
        "disputes",
        ["reference"],
        unique=True,
    )
    op.create_index(
        "ix_disputes_support_case_reference",
        "disputes",
        ["support_case_reference"],
        unique=False,
    )
    op.create_index(
        "ix_disputes_transaction_reference",
        "disputes",
        ["transaction_reference"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_disputes_transaction_reference",
        table_name="disputes",
    )
    op.drop_index(
        "ix_disputes_support_case_reference",
        table_name="disputes",
    )
    op.drop_index(
        "ix_disputes_reference",
        table_name="disputes",
    )
    op.drop_table("disputes")