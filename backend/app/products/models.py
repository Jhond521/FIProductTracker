import uuid
from datetime import date

from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class FinancialProduct(Base):
    """A credit card (walking-skeleton scope: Colombia market only).

    market and day_count_basis are modeled explicitly now, even though
    only Colombia is implemented, so adding the US MarketRulesProfile
    later is additive rather than a schema migration that touches every
    existing row.
    """

    __tablename__ = "financial_products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    market: Mapped[str] = mapped_column(String(2), default="CO")  # ISO-ish market code: CO, US
    institution_name: Mapped[str] = mapped_column(String(120))
    credit_limit: Mapped[float] = mapped_column(Numeric(14, 2))
    ea_rate: Mapped[float] = mapped_column(Numeric(6, 4))  # effective annual rate, e.g. 0.3600
    day_count_basis: Mapped[int] = mapped_column(default=365)  # 360 or 365, per-product

    purchases: Mapped[list["Purchase"]] = relationship(back_populates="product")


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("financial_products.id"))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="COP")
    purchase_date: Mapped[date]
    n_installments: Mapped[int] = mapped_column(default=1)
    interest_free_promo: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    product: Mapped["FinancialProduct"] = relationship(back_populates="purchases")
