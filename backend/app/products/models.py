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

    co_single_installment_charges_interest is the CO-only counterpart:
    whether a "cuota unica" (single-installment) purchase on this card
    carries interest, which varies by issuer.

    recurring_fee, insurance_opt_in/insurance_cost, and fx_fee are common
    to both markets (PRD Section 8) but not yet wired into the interest/
    fee calculations in calculations/ -- they're captured here so the
    Add/Edit Card UI can record them, with the calculation wiring left
    for a follow-up.
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
    statement_cutoff_day: Mapped[int] = mapped_column(default=1)  # Fecha de corte: day of month the statement closes
    payment_due_day: Mapped[int] = mapped_column(default=15)  # Fecha de pago: day of month payment is due
    recurring_fee: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)  # cuota de manejo / annual fee, per statement cycle
    insurance_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    insurance_cost: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)  # per statement cycle, required when insurance_opt_in
    fx_fee: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)  # FX/international transaction fee, e.g. 0.03 for 3%
    co_single_installment_charges_interest: Mapped[bool] = mapped_column(Boolean, default=False)  # CO-only: whether "cuota unica" purchases carry interest

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
