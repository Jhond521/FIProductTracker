import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.calculations.minimum_payment import US_DEFAULT_FLAT_FLOOR
from app.calculations.market_rules import VALID_MARKETS


class FinancialProductCreate(BaseModel):
    market: str = Field(default="CO", max_length=2)
    institution_name: str
    credit_limit: float = Field(gt=0)
    ea_rate: float | None = Field(default=None, ge=0, description="CO: effective annual rate, e.g. 0.36 for 36%")
    day_count_basis: int = Field(default=365, description="360 or 365 — bank-specific, not market-inferred")
    apr: float | None = Field(default=None, ge=0, description="US: annual percentage rate, e.g. 0.24 for 24%")
    penalty_rate: float | None = Field(default=None, ge=0, description="Tasa de mora / penalty APR")
    min_payment_flat_floor: float | None = Field(
        default=None, ge=0, description="US minimum-payment flat-dollar floor"
    )
    installment_plan_available: bool = Field(
        default=False, description="US: whether a Plan It/Flex Pay style feature is offered"
    )
    statement_cutoff_day: int = Field(
        default=1, ge=1, le=28, description="Fecha de corte: day of month the statement closes"
    )
    payment_due_day: int = Field(
        default=15, ge=1, le=28, description="Fecha de pago: day of month payment is due"
    )
    recurring_fee: float | None = Field(
        default=None, ge=0, description="Cuota de manejo / annual fee, charged per statement cycle"
    )
    insurance_opt_in: bool = Field(default=False, description="Common in Colombia; optional add-on in US")
    insurance_cost: float | None = Field(
        default=None, ge=0, description="Per statement cycle; required when insurance_opt_in is true"
    )
    fx_fee: float | None = Field(
        default=None, ge=0, description="FX/international transaction fee, e.g. 0.03 for 3%"
    )
    co_single_installment_charges_interest: bool = Field(
        default=False,
        description="CO only: whether a single-installment (cuota unica) purchase carries interest",
    )

    @model_validator(mode="after")
    def _validate_market_specific_fields(self) -> "FinancialProductCreate":
        if self.market not in VALID_MARKETS:
            raise ValueError(f"market must be one of {VALID_MARKETS}")
        if self.market == "CO" and self.ea_rate is None:
            raise ValueError("ea_rate is required for the CO market")
        if self.market == "US" and self.apr is None:
            raise ValueError("apr is required for the US market")
        if self.market == "US" and self.min_payment_flat_floor is None:
            self.min_payment_flat_floor = US_DEFAULT_FLAT_FLOOR
        if self.insurance_opt_in and self.insurance_cost is None:
            raise ValueError("insurance_cost is required when insurance_opt_in is true")
        return self


class FinancialProductRead(FinancialProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class FinancialProductUpdate(BaseModel):
    """Partial update. `market` is deliberately excluded — changing it after
    creation would invalidate the calculation history (PRD Journey J4)."""

    model_config = ConfigDict(extra="forbid")

    institution_name: str | None = None
    credit_limit: float | None = Field(default=None, gt=0)
    ea_rate: float | None = Field(default=None, ge=0)
    day_count_basis: int | None = None
    apr: float | None = Field(default=None, ge=0)
    penalty_rate: float | None = Field(default=None, ge=0)
    min_payment_flat_floor: float | None = Field(default=None, ge=0)
    installment_plan_available: bool | None = None
    statement_cutoff_day: int | None = Field(default=None, ge=1, le=28)
    payment_due_day: int | None = Field(default=None, ge=1, le=28)
    recurring_fee: float | None = Field(default=None, ge=0)
    insurance_opt_in: bool | None = None
    insurance_cost: float | None = Field(default=None, ge=0)
    fx_fee: float | None = Field(default=None, ge=0)
    co_single_installment_charges_interest: bool | None = None


class PurchaseCreate(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(default="COP", max_length=3)
    purchase_date: date
    n_installments: int = Field(default=1, ge=1)
    interest_free_promo: bool = False
    description: str | None = None


class PurchaseRead(PurchaseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    product_id: uuid.UUID


class PurchaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, max_length=3)
    purchase_date: date | None = None
    n_installments: int | None = Field(default=None, ge=1)
    interest_free_promo: bool | None = None
    description: str | None = None


class InstallmentEntryRead(BaseModel):
    installment_number: int
    payment: float
    principal_portion: float
    interest_portion: float
    remaining_balance: float


class PurchaseScheduleRead(BaseModel):
    purchase_id: uuid.UUID
    total_interest_cost: float
    real_annualized_cost: float
    schedule: list[InstallmentEntryRead]


class PurchaseContributionRead(BaseModel):
    purchase_id: uuid.UUID
    description: str | None
    principal_portion: float
    interest_portion: float


class StatementPeriodSummaryRead(BaseModel):
    period_start: date
    period_end: date
    due_date: date
    total_principal: float
    total_interest: float
    total_fees: float
    total_due: float


class StatementPeriodDetailRead(StatementPeriodSummaryRead):
    contributions: list[PurchaseContributionRead]
