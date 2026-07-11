import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.calculations.amortization import (
    amortize_fixed_installments,
    real_annualized_cost,
    total_interest_cost,
)
from app.calculations.rates import ea_to_monthly_rate
from app.core.db import get_db
from app.products.models import FinancialProduct, Purchase
from app.products.schemas import (
    FinancialProductCreate,
    FinancialProductRead,
    FinancialProductUpdate,
    InstallmentEntryRead,
    PurchaseCreate,
    PurchaseRead,
    PurchaseScheduleRead,
    PurchaseUpdate,
)

router = APIRouter(prefix="/products", tags=["products"])


async def _get_owned_product(
    product_id: uuid.UUID, current_user: User, db: AsyncSession
) -> FinancialProduct:
    product = await db.get(FinancialProduct, product_id)
    if not product or product.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


async def _get_owned_purchase(
    product_id: uuid.UUID, purchase_id: uuid.UUID, current_user: User, db: AsyncSession
) -> Purchase:
    await _get_owned_product(product_id, current_user, db)
    purchase = await db.get(Purchase, purchase_id)
    if not purchase or purchase.product_id != product_id:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase


@router.post("", response_model=FinancialProductRead, status_code=201)
async def create_product(
    payload: FinancialProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = FinancialProduct(**payload.model_dump(), owner_id=current_user.id)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("", response_model=list[FinancialProductRead])
async def list_products(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(FinancialProduct).where(FinancialProduct.owner_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{product_id}", response_model=FinancialProductRead)
async def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_owned_product(product_id, current_user, db)


@router.patch("/{product_id}", response_model=FinancialProductRead)
async def update_product(
    product_id: uuid.UUID,
    payload: FinancialProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await _get_owned_product(product_id, current_user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    return product


@router.post("/{product_id}/purchases", response_model=PurchaseRead, status_code=201)
async def create_purchase(
    product_id: uuid.UUID,
    payload: PurchaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_product(product_id, current_user, db)

    purchase = Purchase(product_id=product_id, **payload.model_dump())
    db.add(purchase)
    await db.commit()
    await db.refresh(purchase)
    return purchase


@router.get("/{product_id}/purchases", response_model=list[PurchaseRead])
async def list_purchases(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_product(product_id, current_user, db)

    result = await db.execute(select(Purchase).where(Purchase.product_id == product_id))
    return result.scalars().all()


@router.patch("/{product_id}/purchases/{purchase_id}", response_model=PurchaseRead)
async def update_purchase(
    product_id: uuid.UUID,
    purchase_id: uuid.UUID,
    payload: PurchaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    purchase = await _get_owned_purchase(product_id, purchase_id, current_user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(purchase, field, value)
    await db.commit()
    await db.refresh(purchase)
    return purchase


@router.get("/{product_id}/purchases/{purchase_id}/schedule", response_model=PurchaseScheduleRead)
async def get_purchase_schedule(
    product_id: uuid.UUID,
    purchase_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_product(product_id, current_user, db)

    result = await db.execute(
        select(Purchase, FinancialProduct)
        .join(FinancialProduct, Purchase.product_id == FinancialProduct.id)
        .where(Purchase.id == purchase_id, Purchase.product_id == product_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Purchase not found")
    purchase, product = row

    # Schedule is always computed fresh from current field values, never
    # persisted — an edit is naturally reflected everywhere on next read,
    # with no separate "recalculate" step or forward/retroactive split.
    monthly_rate = 0.0 if purchase.interest_free_promo else ea_to_monthly_rate(float(product.ea_rate))
    schedule = amortize_fixed_installments(
        principal=float(purchase.amount),
        monthly_rate=monthly_rate,
        n_installments=purchase.n_installments,
    )

    return PurchaseScheduleRead(
        purchase_id=purchase.id,
        total_interest_cost=total_interest_cost(schedule),
        real_annualized_cost=real_annualized_cost(float(purchase.amount), schedule),
        schedule=[InstallmentEntryRead(**entry.__dict__) for entry in schedule],
    )
