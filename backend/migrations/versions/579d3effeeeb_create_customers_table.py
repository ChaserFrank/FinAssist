"""create customers table

Revision ID: 579d3effeeeb
Revises: ab5cdd984c28
Create Date: 2026-09-28 14:12:59.525721

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "579d3effeeeb"
down_revision: str | None = "ab5cdd984c28"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference"),
    )
    op.create_index(
        "ix_customers_reference",
        "customers",
        ["reference"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_customers_reference", table_name="customers")
    op.drop_table("customers")