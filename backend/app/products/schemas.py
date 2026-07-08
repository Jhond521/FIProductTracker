import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class FinancialProductCreate(BaseModel):
    market: str = Field(default="CO", max_length=2)
    institution_name: str
    credit_limit: float = Field(gt=0)
    ea_rate: float = Field(ge=0, description="Effective annual rate, e.g. 0.36 for 36%")
    day_count_basis: int = Field(default=365, description="360 or 365 — bank-specific, not market-inferred")


class FinancialProductRead(FinancialProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


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
