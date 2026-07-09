"""add users table and financial_products.owner_id

Revision ID: 0002_add_users_and_product_owner
Revises: 0001_initial
Create Date: 2026-07-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_users_and_product_owner"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Placeholder owner for any financial_products created before auth existed
# (e.g. manual walking-skeleton testing) — lets owner_id become NOT NULL
# without discarding pre-existing rows.
LEGACY_USER_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("google_sub", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("picture_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.execute(
        sa.text(
            "INSERT INTO users (id, google_sub, email, name, created_at) "
            "VALUES (:id, 'legacy-placeholder', 'legacy-data@local', 'Legacy Data', now())"
        ).bindparams(sa.bindparam("id", value=LEGACY_USER_ID, type_=sa.Uuid()))
    )

    op.add_column("financial_products", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.execute(
        sa.text("UPDATE financial_products SET owner_id = :id WHERE owner_id IS NULL").bindparams(
            sa.bindparam("id", value=LEGACY_USER_ID, type_=sa.Uuid())
        )
    )
    op.alter_column("financial_products", "owner_id", nullable=False)
    op.create_foreign_key(
        "fk_financial_products_owner_id_users",
        "financial_products",
        "users",
        ["owner_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_financial_products_owner_id_users", "financial_products", type_="foreignkey"
    )
    op.drop_column("financial_products", "owner_id")
    op.execute(
        sa.text("DELETE FROM users WHERE id = :id").bindparams(
            sa.bindparam("id", value=LEGACY_USER_ID, type_=sa.Uuid())
        )
    )
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_google_sub", table_name="users")
    op.drop_table("users")
