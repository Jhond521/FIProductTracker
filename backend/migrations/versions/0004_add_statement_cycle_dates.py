"""add statement cycle dates to financial_products

Revision ID: 0004_add_statement_cycle_dates
Revises: 0003_add_us_market_fields
Create Date: 2026-07-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_add_statement_cycle_dates"
down_revision: Union[str, None] = "0003_add_us_market_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "financial_products",
        sa.Column("statement_cutoff_day", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "financial_products",
        sa.Column("payment_due_day", sa.Integer(), nullable=False, server_default="15"),
    )


def downgrade() -> None:
    op.drop_column("financial_products", "payment_due_day")
    op.drop_column("financial_products", "statement_cutoff_day")
