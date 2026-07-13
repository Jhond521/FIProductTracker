"""
Deterministic, rule-based recommendations (PRD Section 7.6, Journey J5).

Every rule reuses existing calculation primitives (amortization,
market_rules, statement_periods) rather than re-deriving numbers, so a
recommendation's numbers always match what the rest of the app shows for
the same purchase/period.

Two PRD-listed rules -- "interest-cost delta between minimum payment and
a higher payment" and "paying the full statement balance would eliminate
interest" -- collapse into one `PayInFullSavesInterestFlag`: both are the
same insight (this cycle's interest is what a full payment, rather than
the minimum, avoids going forward). It's US-only: CO's cuotas are fixed
at purchase time via `amortize_fixed_installments`, so paying more than
the scheduled installment doesn't change interest already baked into the
schedule -- "pay more to save interest" isn't a real lever in this model
for CO, so faking a CO version of this flag would be dishonest about
what the app actually models.

Similarly, "installment promo/plan terms nearing completion" is CO-only
here: CO's `interest_free_promo` purchases have a known schedule length
to track, but there's no per-purchase field yet capturing a US
installment-plan's opt-in/terms (PRD Section 8 lists this as a real gap,
not something this module can work around).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

from app.calculations.amortization import real_annualized_cost
from app.calculations.market_rules import get_market_rules
from app.calculations.minimum_payment import US_DEFAULT_FLAT_FLOOR
from app.calculations.statement_periods import (
    PeriodPurchaseInput,
    list_statement_periods,
    outstanding_balance,
    period_shifted,
    statement_period_containing,
)

UTILIZATION_RISK_THRESHOLD = 0.30  # PRD: "utilization above a threshold" -- common personal-finance guideline
PROMO_EXPIRING_INSTALLMENTS_REMAINING = 1  # flag when this many or fewer installments remain


@dataclass(frozen=True)
class RecommendationProductInput:
    product_id: uuid.UUID
    institution_name: str
    market: str
    credit_limit: float
    ea_rate: float | None
    apr: float | None
    day_count_basis: int
    cutoff_day: int
    payment_due_day: int
    min_payment_flat_floor: float | None
    purchases: list[PeriodPurchaseInput]


@dataclass(frozen=True)
class RealCostExceedsRateFlag:
    product_id: uuid.UUID
    purchase_id: uuid.UUID
    description: str | None
    real_annualized_cost: float
    disclosed_rate: float


@dataclass(frozen=True)
class PayInFullSavesInterestFlag:
    product_id: uuid.UUID
    current_period_interest: float
    minimum_payment: float
    statement_balance: float


@dataclass(frozen=True)
class PromoExpiringFlag:
    product_id: uuid.UUID
    purchase_id: uuid.UUID
    description: str | None
    installments_remaining: int


@dataclass(frozen=True)
class PayoffRankEntry:
    product_id: uuid.UUID
    institution_name: str
    disclosed_rate: float
    outstanding_balance: float


@dataclass(frozen=True)
class UtilizationRiskFlag:
    product_id: uuid.UUID
    utilization: float
    threshold: float = UTILIZATION_RISK_THRESHOLD


@dataclass(frozen=True)
class RecommendationSet:
    real_cost_exceeds_rate: list[RealCostExceedsRateFlag] = field(default_factory=list)
    pay_in_full_saves_interest: list[PayInFullSavesInterestFlag] = field(default_factory=list)
    promo_expiring: list[PromoExpiringFlag] = field(default_factory=list)
    avalanche_payoff_order: list[PayoffRankEntry] = field(default_factory=list)
    utilization_risk: list[UtilizationRiskFlag] = field(default_factory=list)


def _flag_real_cost_exceeds_rate(
    product: RecommendationProductInput,
) -> list[RealCostExceedsRateFlag]:
    """CO: compares each non-promo purchase's real annualized cost (total
    interest relative to principal, annualized by schedule length) against
    the card's disclosed EA. In today's model this comparison structurally
    never fires: `real_annualized_cost` is a simple linear annualization
    (see its docstring), which is mathematically always <= the compounded
    EA it's derived from, and no purchase-level fees are wired into
    interest yet either. The comparison is kept -- and correct -- because
    it's meant to start doing real work automatically once
    `real_annualized_cost` moves to an IRR-based calculation or per-
    purchase fees land, without this rule needing to change. US purchases
    always cost exactly the disclosed APR in this model (no per-purchase
    promo mechanism exists for US), so this never meaningfully triggers
    there either."""
    if product.market != "CO" or product.ea_rate is None:
        return []

    rules = get_market_rules("CO")
    flags: list[RealCostExceedsRateFlag] = []

    for purchase in product.purchases:
        if purchase.interest_free_promo:
            continue
        schedule = rules.compute_interest(
            principal=purchase.amount,
            ea_rate=product.ea_rate,
            n_installments=purchase.n_installments,
            interest_free_promo=False,
        )
        cost = real_annualized_cost(purchase.amount, schedule)
        if cost > product.ea_rate:
            flags.append(
                RealCostExceedsRateFlag(
                    product_id=product.product_id,
                    purchase_id=purchase.purchase_id,
                    description=purchase.description,
                    real_annualized_cost=cost,
                    disclosed_rate=product.ea_rate,
                )
            )

    return flags


def _flag_pay_in_full_saves_interest(
    product: RecommendationProductInput, as_of: date
) -> list[PayInFullSavesInterestFlag]:
    if product.market != "US" or product.apr is None:
        return []

    periods = list_statement_periods(
        market="US",
        cutoff_day=product.cutoff_day,
        payment_due_day=product.payment_due_day,
        ea_rate=None,
        apr=product.apr,
        day_count_basis=product.day_count_basis,
        purchases=product.purchases,
        as_of=as_of,
    )
    if not periods or periods[0].total_interest <= 0:
        return []
    current_period = periods[0]

    balance = outstanding_balance(
        market="US",
        cutoff_day=product.cutoff_day,
        payment_due_day=product.payment_due_day,
        ea_rate=None,
        purchases=product.purchases,
        as_of=as_of,
    )
    rules = get_market_rules("US")
    minimum_payment = rules.compute_minimum_payment(
        statement_balance=balance,
        period_interest=current_period.total_interest,
        period_fees=current_period.total_fees,
        flat_floor=product.min_payment_flat_floor or US_DEFAULT_FLAT_FLOOR,
    )

    return [
        PayInFullSavesInterestFlag(
            product_id=product.product_id,
            current_period_interest=current_period.total_interest,
            minimum_payment=minimum_payment,
            statement_balance=balance,
        )
    ]


def _flag_promo_expiring(
    product: RecommendationProductInput, as_of: date
) -> list[PromoExpiringFlag]:
    if product.market != "CO":
        return []

    flags: list[PromoExpiringFlag] = []
    for purchase in product.purchases:
        if not purchase.interest_free_promo:
            continue
        first_period = statement_period_containing(
            purchase.purchase_date, product.cutoff_day, product.payment_due_day
        )
        elapsed = sum(
            1
            for i in range(purchase.n_installments)
            if period_shifted(first_period, i, product.cutoff_day, product.payment_due_day).period_end
            <= as_of
        )
        remaining = purchase.n_installments - elapsed
        if 0 < remaining <= PROMO_EXPIRING_INSTALLMENTS_REMAINING:
            flags.append(
                PromoExpiringFlag(
                    product_id=product.product_id,
                    purchase_id=purchase.purchase_id,
                    description=purchase.description,
                    installments_remaining=remaining,
                )
            )

    return flags


def _avalanche_payoff_order(
    products: list[RecommendationProductInput], as_of: date
) -> list[PayoffRankEntry]:
    """Ranks cards with an outstanding balance by disclosed rate (EA for
    CO, APR for US) descending -- same rough-magnitude cross-market
    comparison already used for the dashboard's highest-cost flag."""
    entries: list[PayoffRankEntry] = []

    for product in products:
        rate = product.ea_rate if product.market == "CO" else product.apr
        if rate is None:
            continue
        balance = outstanding_balance(
            market=product.market,
            cutoff_day=product.cutoff_day,
            payment_due_day=product.payment_due_day,
            ea_rate=product.ea_rate,
            purchases=product.purchases,
            as_of=as_of,
        )
        if balance <= 0:
            continue
        entries.append(
            PayoffRankEntry(
                product_id=product.product_id,
                institution_name=product.institution_name,
                disclosed_rate=rate,
                outstanding_balance=balance,
            )
        )

    return sorted(entries, key=lambda e: e.disclosed_rate, reverse=True)


def _flag_utilization_risk(
    product: RecommendationProductInput, as_of: date
) -> list[UtilizationRiskFlag]:
    if product.credit_limit <= 0:
        return []

    balance = outstanding_balance(
        market=product.market,
        cutoff_day=product.cutoff_day,
        payment_due_day=product.payment_due_day,
        ea_rate=product.ea_rate,
        purchases=product.purchases,
        as_of=as_of,
    )
    utilization = balance / product.credit_limit
    if utilization > UTILIZATION_RISK_THRESHOLD:
        return [UtilizationRiskFlag(product_id=product.product_id, utilization=round(utilization, 4))]
    return []


def build_recommendations(
    products: list[RecommendationProductInput], as_of: date
) -> RecommendationSet:
    real_cost_exceeds_rate: list[RealCostExceedsRateFlag] = []
    pay_in_full_saves_interest: list[PayInFullSavesInterestFlag] = []
    promo_expiring: list[PromoExpiringFlag] = []
    utilization_risk: list[UtilizationRiskFlag] = []

    for product in products:
        real_cost_exceeds_rate += _flag_real_cost_exceeds_rate(product)
        pay_in_full_saves_interest += _flag_pay_in_full_saves_interest(product, as_of)
        promo_expiring += _flag_promo_expiring(product, as_of)
        utilization_risk += _flag_utilization_risk(product, as_of)

    return RecommendationSet(
        real_cost_exceeds_rate=real_cost_exceeds_rate,
        pay_in_full_saves_interest=pay_in_full_saves_interest,
        promo_expiring=promo_expiring,
        avalanche_payoff_order=_avalanche_payoff_order(products, as_of),
        utilization_risk=utilization_risk,
    )
