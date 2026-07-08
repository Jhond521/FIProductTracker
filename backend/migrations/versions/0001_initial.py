"""initial schema: financial_products and purchases

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "financial_products",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("market", sa.String(length=2), nullable=False, server_default="CO"),
        sa.Column("institution_name", sa.String(length=120), nullable=False),
        sa.Column("credit_limit", sa.Numeric(14, 2), nullable=False),
        sa.Column("ea_rate", sa.Numeric(6, 4), nullable=False),
        sa.Column("day_count_basis", sa.Integer(), nullable=False, server_default="365"),
    )

    op.create_table(
        "purchases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "product_id",
            sa.Uuid(),
            sa.ForeignKey("financial_products.id"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="COP"),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("n_installments", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("interest_free_promo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("description", sa.String(length=200), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("purchases")
    op.drop_table("financial_products")
