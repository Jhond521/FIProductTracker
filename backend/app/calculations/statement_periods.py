"""
Statement-period assignment and period-level statement construction
(PRD Section 7.5, Journey J2).

A statement period is bounded by two consecutive occurrences of a card's
cutoff day (`statement_cutoff_day`, "fecha de corte"): purchases made on or
before the cutoff land in the period closing on that cutoff; purchases made
after it land in the *next* period. This grouping is market-agnostic — what
differs per market is how a period's principal/interest total is computed,
so that part is delegated to `MarketRulesProfile` (calculations/market_rules.py)
rather than branched inline here.

`statement_cutoff_day` and `payment_due_day` are restricted to 1-28 at the
schema layer specifically so month-length (Feb 30, Apr 31, ...) never has to
be clamped here — every calendar month has a day 1-28.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta

from app.calculations.average_daily_balance import average_daily_balance
from app.calculations.market_rules import get_market_rules


@dataclass(frozen=True)
class StatementPeriod:
    period_start: date
    period_end: date
    due_date: date


@dataclass(frozen=True)
class PeriodPurchaseInput:
    purchase_id: uuid.UUID
    amount: float
    purchase_date: date
    n_installments: int
    interest_free_promo: bool = False
    description: str | None = None


@dataclass(frozen=True)
class PurchaseContribution:
    purchase_id: uuid.UUID
    description: str | None
    principal_portion: float
    interest_portion: float


@dataclass(frozen=True)
class PeriodStatement:
    period_start: date
    period_end: date
    due_date: date
    total_principal: float
    total_interest: float
    total_fees: float
    total_due: float
    contributions: list[PurchaseContribution] = field(default_factory=list)


def _shift_months(d: date, months: int) -> date:
    """Shift `d` by a whole number of calendar months, keeping the same
    day-of-month. Safe without clamping because callers only ever pass
    day-of-month values in 1-28."""
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    return date(year, month, d.day)


def _cutoff_on_or_after(d: date, cutoff_day: int) -> date:
    same_month_cutoff = date(d.year, d.month, cutoff_day)
    if d.day <= cutoff_day:
        return same_month_cutoff
    return _shift_months(same_month_cutoff, 1)


def _next_occurrence_after(after: date, day: int) -> date:
    candidate = date(after.year, after.month, day)
    if candidate <= after:
        candidate = _shift_months(candidate, 1)
    return candidate


def statement_period_containing(
    reference_date: date, cutoff_day: int, payment_due_day: int
) -> StatementPeriod:
    """The statement period that `reference_date` falls into, given the
    card's cutoff day. A purchase after the cutoff lands in the next
    period (PRD Section 7.5 edge case)."""
    period_end = _cutoff_on_or_after(reference_date, cutoff_day)
    period_start = _shift_months(period_end, -1) + timedelta(days=1)
    due_date = _next_occurrence_after(period_end, payment_due_day)
    return StatementPeriod(period_start=period_start, period_end=period_end, due_date=due_date)


def period_shifted(
    period: StatementPeriod, n_cycles: int, cutoff_day: int, payment_due_day: int
) -> StatementPeriod:
    """The statement period `n_cycles` billing cycles after `period`."""
    period_end = _shift_months(period.period_end, n_cycles)
    period_start = _shift_months(period_end, -1) + timedelta(days=1)
    due_date = _next_occurrence_after(period_end, payment_due_day)
    return StatementPeriod(period_start=period_start, period_end=period_end, due_date=due_date)


def build_co_period_statement(
    *,
    cutoff_day: int,
    payment_due_day: int,
    ea_rate: float,
    purchases: list[PeriodPurchaseInput],
    target_period_end: date,
) -> PeriodStatement:
    """Colombia: each purchase carries its own fixed-installment (cuota
    fija) schedule; a period's total is whichever installment of each
    purchase falls in that period."""
    rules = get_market_rules("CO")
    contributions: list[PurchaseContribution] = []

    for purchase in purchases:
        first_period = statement_period_containing(
            purchase.purchase_date, cutoff_day, payment_due_day
        )
        schedule = rules.compute_interest(
            principal=purchase.amount,
            ea_rate=ea_rate,
            n_installments=purchase.n_installments,
            interest_free_promo=purchase.interest_free_promo,
        )
        for i, entry in enumerate(schedule):
            installment_period = period_shifted(first_period, i, cutoff_day, payment_due_day)
            if installment_period.period_end == target_period_end:
                contributions.append(
                    PurchaseContribution(
                        purchase_id=purchase.purchase_id,
                        description=purchase.description,
                        principal_portion=entry.principal_portion,
                        interest_portion=entry.interest_portion,
                    )
                )
                break

    return _totals(target_period_end, payment_due_day, contributions)


def build_us_period_statement(
    *,
    cutoff_day: int,
    payment_due_day: int,
    apr: float,
    day_count_basis: int,
    purchases: list[PeriodPurchaseInput],
    target_period_end: date,
) -> PeriodStatement:
    """US: a single revolving balance across the whole billing cycle,
    charged interest via average-daily-balance against the disclosed APR.
    With no payment-tracking model yet, every purchase is treated as
    still outstanding (a known simplification until payments are
    modeled) -- so the daily balance is the running sum of purchases made
    on or before each day of the cycle."""
    rules = get_market_rules("US")
    period_start = _shift_months(target_period_end, -1) + timedelta(days=1)
    days_in_cycle = (target_period_end - period_start).days + 1

    daily_balances = []
    day = period_start
    while day <= target_period_end:
        daily_balances.append(sum(p.amount for p in purchases if p.purchase_date <= day))
        day += timedelta(days=1)

    adb = average_daily_balance(daily_balances)
    interest = rules.compute_interest(
        average_daily_balance_amount=adb,
        apr=apr,
        day_count_basis=day_count_basis,
        days_in_cycle=days_in_cycle,
    )

    contributions = [
        PurchaseContribution(
            purchase_id=p.purchase_id,
            description=p.description,
            principal_portion=round(p.amount, 2),
            interest_portion=0.0,
        )
        for p in purchases
        if period_start <= p.purchase_date <= target_period_end
    ]

    statement = _totals(target_period_end, payment_due_day, contributions)
    # Interest is a whole-cycle revolving charge, not attributable to one
    # purchase, so it's added at the period level rather than split across
    # `contributions`.
    return PeriodStatement(
        period_start=statement.period_start,
        period_end=statement.period_end,
        due_date=statement.due_date,
        total_principal=statement.total_principal,
        total_interest=interest,
        total_fees=0.0,
        total_due=round(statement.total_principal + interest, 2),
        contributions=statement.contributions,
    )


def _totals(
    target_period_end: date, payment_due_day: int, contributions: list[PurchaseContribution]
) -> PeriodStatement:
    period_start = _shift_months(target_period_end, -1) + timedelta(days=1)
    due_date = _next_occurrence_after(target_period_end, payment_due_day)
    total_principal = round(sum(c.principal_portion for c in contributions), 2)
    total_interest = round(sum(c.interest_portion for c in contributions), 2)
    return PeriodStatement(
        period_start=period_start,
        period_end=target_period_end,
        due_date=due_date,
        total_principal=total_principal,
        total_interest=total_interest,
        total_fees=0.0,
        total_due=round(total_principal + total_interest, 2),
        contributions=contributions,
    )


def build_statement_period(
    *,
    market: str,
    cutoff_day: int,
    payment_due_day: int,
    ea_rate: float | None,
    apr: float | None,
    day_count_basis: int,
    purchases: list[PeriodPurchaseInput],
    target_period_end: date,
) -> PeriodStatement:
    """Dispatch to the market-appropriate period builder. The two markets'
    inputs are genuinely different shapes (installment terms vs. a
    billing-cycle APR), matching the same rationale as
    `MarketRulesProfile` for taking market-specific kwargs rather than a
    forced shared signature."""
    if market == "CO":
        return build_co_period_statement(
            cutoff_day=cutoff_day,
            payment_due_day=payment_due_day,
            ea_rate=ea_rate,
            purchases=purchases,
            target_period_end=target_period_end,
        )
    if market == "US":
        return build_us_period_statement(
            cutoff_day=cutoff_day,
            payment_due_day=payment_due_day,
            apr=apr,
            day_count_basis=day_count_basis,
            purchases=purchases,
            target_period_end=target_period_end,
        )
    raise ValueError(f"Unknown market {market!r}")


def list_statement_periods(
    *,
    market: str,
    cutoff_day: int,
    payment_due_day: int,
    ea_rate: float | None,
    apr: float | None,
    day_count_basis: int,
    purchases: list[PeriodPurchaseInput],
    as_of: date,
) -> list[PeriodStatement]:
    """Every statement period with activity, from the card's earliest
    purchase through the period containing `as_of`, newest first."""
    if not purchases:
        return []

    earliest_date = min(p.purchase_date for p in purchases)
    period = statement_period_containing(earliest_date, cutoff_day, payment_due_day)
    current_period_end = statement_period_containing(as_of, cutoff_day, payment_due_day).period_end

    periods: list[PeriodStatement] = []
    while period.period_end <= current_period_end:
        statement = build_statement_period(
            market=market,
            cutoff_day=cutoff_day,
            payment_due_day=payment_due_day,
            ea_rate=ea_rate,
            apr=apr,
            day_count_basis=day_count_basis,
            purchases=purchases,
            target_period_end=period.period_end,
        )
        # US periods can carry a nonzero balance and accrue interest with
        # no new contributions that cycle (no payment tracking yet), so
        # `total_due` is the right inclusion check, not just contributions.
        if statement.contributions or statement.total_due:
            periods.append(statement)
        period = period_shifted(period, 1, cutoff_day, payment_due_day)

    return sorted(periods, key=lambda s: s.period_end, reverse=True)
