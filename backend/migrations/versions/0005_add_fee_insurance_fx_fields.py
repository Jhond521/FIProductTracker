"""add recurring fee, insurance, FX fee, and CO single-installment fields to financial_products

Revision ID: 0005_add_fee_insurance_fx_fields
Revises: 0004_add_statement_cycle_dates
Create Date: 2026-07-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_add_fee_insurance_fx_fields"
down_revision: Union[str, None] = "0004_add_statement_cycle_dates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "financial_products", sa.Column("recurring_fee", sa.Numeric(10, 2), nullable=True)
    )
    op.add_column(
        "financial_products",
        sa.Column("insurance_opt_in", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "financial_products", sa.Column("insurance_cost", sa.Numeric(10, 2), nullable=True)
    )
    op.add_column("financial_products", sa.Column("fx_fee", sa.Numeric(6, 4), nullable=True))
    op.add_column(
        "financial_products",
        sa.Column(
            "co_single_installment_charges_interest",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("financial_products", "co_single_installment_charges_interest")
    op.drop_column("financial_products", "fx_fee")
    op.drop_column("financial_products", "insurance_cost")
    op.drop_column("financial_products", "insurance_opt_in")
    op.drop_column("financial_products", "recurring_fee")
