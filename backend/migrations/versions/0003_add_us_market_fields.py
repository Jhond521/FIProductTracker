"""add US-market fields to financial_products

Revision ID: 0003_add_us_market_fields
Revises: 0002_add_users_and_product_owner
Create Date: 2026-07-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_us_market_fields"
down_revision: Union[str, None] = "0002_add_users_and_product_owner"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ea_rate is CO-only; US rows have no EA disclosure, so it must become
    # nullable rather than defaulted -- a defaulted value would look like a
    # real disclosed rate to the calculation engine.
    op.alter_column("financial_products", "ea_rate", nullable=True)

    op.add_column("financial_products", sa.Column("apr", sa.Numeric(6, 4), nullable=True))
    op.add_column("financial_products", sa.Column("penalty_rate", sa.Numeric(6, 4), nullable=True))
    op.add_column(
        "financial_products", sa.Column("min_payment_flat_floor", sa.Numeric(8, 2), nullable=True)
    )
    op.add_column(
        "financial_products",
        sa.Column(
            "installment_plan_available", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )


def downgrade() -> None:
    op.drop_column("financial_products", "installment_plan_available")
    op.drop_column("financial_products", "min_payment_flat_floor")
    op.drop_column("financial_products", "penalty_rate")
    op.drop_column("financial_products", "apr")
    op.alter_column("financial_products", "ea_rate", nullable=False)
