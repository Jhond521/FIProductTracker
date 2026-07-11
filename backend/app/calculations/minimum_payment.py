"""
Minimum-payment formulas, one per market — structurally different, per
PRD Section 5: Colombia's is a regulated interest+fees+principal shape
already satisfied by each purchase's fixed installment (cuota); the US
has no central regulator but issuers converge on a common shape
(PRD Section 10).
"""

from __future__ import annotations

US_DEFAULT_FLAT_FLOOR = 25.0  # Wells Fargo / Bank of America / Capital One shape


def us_minimum_payment(
    *,
    statement_balance: float,
    period_interest: float,
    period_fees: float,
    past_due_amount: float = 0.0,
    flat_floor: float = US_DEFAULT_FLAT_FLOOR,
) -> float:
    """PRD Section 10 reference formula:

        minimum_payment = past_due_amount
            + max(flat_floor, 0.01 * statement_balance + period_interest + period_fees)

    `flat_floor` is per-card configurable (varies by issuer), defaulting to
    the MVP reference value shared by Wells Fargo/Bank of America/Capital One.
    """
    if statement_balance < 0:
        raise ValueError("statement_balance cannot be negative")
    if period_interest < 0 or period_fees < 0:
        raise ValueError("period_interest and period_fees cannot be negative")
    if past_due_amount < 0:
        raise ValueError("past_due_amount cannot be negative")
    if flat_floor < 0:
        raise ValueError("flat_floor cannot be negative")

    percentage_leg = 0.01 * statement_balance + period_interest + period_fees
    return round(past_due_amount + max(flat_floor, percentage_leg), 2)


def colombia_minimum_payment(
    period_installment_payments: list[float],
    period_fees: float = 0.0,
) -> float:
    """Colombia's regulated minimum (interest + fees + required principal)
    is already satisfied by the sum of that period's fixed cuota payments —
    each purchase's amortization schedule bakes principal and interest
    together per installment — plus any recurring fee (cuota de manejo)."""
    if period_fees < 0:
        raise ValueError("period_fees cannot be negative")
    if any(payment < 0 for payment in period_installment_payments):
        raise ValueError("period_installment_payments cannot contain negative amounts")

    return round(sum(period_installment_payments) + period_fees, 2)
