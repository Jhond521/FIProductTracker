"""
Rate conversion utilities.

Colombian banks disclose EA (effective annual rate). Everything else
(daily accrual, monthly amortization) is derived from EA via geometric
(compounding) conversion — never simple/linear conversion, which would
misstate the real cost.

day_count_basis is a per-product setting (360 or 365), not a per-market
default: Colombian banks each choose independently how they compute daily
interest, so this must be configurable per FinancialProduct rather than
inferred from the country.
"""

from __future__ import annotations

VALID_DAY_COUNT_BASES = (360, 365)


def ea_to_periodic_rate(ea: float, periods_per_year: float) -> float:
    """Convert an effective annual rate into an effective rate for any
    compounding period, using geometric conversion.

    periods_per_year examples: 365 or 360 for daily, 12 for monthly.
    """
    if ea <= -1:
        raise ValueError("EA must be greater than -100%")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    return (1 + ea) ** (1 / periods_per_year) - 1


def ea_to_daily_rate(ea: float, day_count_basis: int = 365) -> float:
    """Convert EA to a daily periodic rate, using the product's own
    day-count basis (360 or 365) rather than assuming one per market."""
    if day_count_basis not in VALID_DAY_COUNT_BASES:
        raise ValueError(
            f"day_count_basis must be one of {VALID_DAY_COUNT_BASES}, got {day_count_basis}"
        )
    return ea_to_periodic_rate(ea, day_count_basis)


def ea_to_monthly_rate(ea: float) -> float:
    """Convert EA to a monthly periodic rate — used for installment
    amortization schedules (cuotas), independent of day_count_basis."""
    return ea_to_periodic_rate(ea, 12)
