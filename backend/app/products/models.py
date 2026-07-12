import uuid
from datetime import date

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class FinancialProduct(Base):
    """A credit card, Colombia or US market.

    ea_rate is CO-only (nullable so US rows don't carry it); apr,
    penalty_rate, min_payment_flat_floor, and installment_plan_available
    are the US-side fields selected by the MarketRulesProfile abstraction
    (see calculations/market_rules.py) once market == "US".
    """

    __tablename__ = "financial_products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    market: Mapped[str] = mapped_column(String(2), default="CO")  # ISO-ish market code: CO, US
    institution_name: Mapped[str] = mapped_column(String(120))
    credit_limit: Mapped[float] = mapped_column(Numeric(14, 2))
    ea_rate: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)  # CO: effective annual rate, e.g. 0.3600
    day_count_basis: Mapped[int] = mapped_column(default=365)  # 360 or 365, per-product
    apr: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)  # US: annual percentage rate
    penalty_rate: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)  # tasa de mora / penalty APR
    min_payment_flat_floor: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)  # US minimum-payment floor
    installment_plan_available: Mapped[bool] = mapped_column(Boolean, default=False)  # US Plan It/Flex Pay style feature

    owner: Mapped["User"] = relationship(back_populates="products")  # noqa: F821
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
