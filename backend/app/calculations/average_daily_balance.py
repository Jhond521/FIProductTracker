"""
Average-daily-balance (ADB) interest calculation — the US revolving-credit
method, computed against a single disclosed APR for the whole billing cycle
(as opposed to Colombia's per-purchase installment accrual).

APR is a nominal annual rate by US convention: the daily periodic rate is
the simple linear division `apr / day_count_basis`, never the geometric
EA conversion used for Colombian effective-annual rates in
`calculations/rates.py`. Mixing the two conventions would misstate the
real cost in both directions.
"""

from __future__ import annotations

from app.calculations.rates import VALID_DAY_COUNT_BASES


def average_daily_balance(daily_balances: list[float]) -> float:
    """Mean of the account's balance on each day of the billing cycle."""
    if not daily_balances:
        raise ValueError("daily_balances must not be empty")
    return sum(daily_balances) / len(daily_balances)


def apr_to_daily_rate(apr: float, day_count_basis: int = 365) -> float:
    """Convert an APR to a daily periodic rate via simple division —
    the US convention, not the geometric conversion used for CO's EA."""
    if apr < 0:
        raise ValueError("apr cannot be negative")
    if day_count_basis not in VALID_DAY_COUNT_BASES:
        raise ValueError(
            f"day_count_basis must be one of {VALID_DAY_COUNT_BASES}, got {day_count_basis}"
        )
    return apr / day_count_basis


def adb_interest_charge(
    average_daily_balance_amount: float,
    apr: float,
    day_count_basis: int,
    days_in_cycle: int,
) -> float:
    """Interest charged for one billing cycle under the average-daily-balance
    method: avg_daily_balance * daily_rate * days_in_cycle."""
    if average_daily_balance_amount < 0:
        raise ValueError("average_daily_balance_amount cannot be negative")
    if days_in_cycle <= 0:
        raise ValueError("days_in_cycle must be a positive integer")

    daily_rate = apr_to_daily_rate(apr, day_count_basis)
    return round(average_daily_balance_amount * daily_rate * days_in_cycle, 2)
