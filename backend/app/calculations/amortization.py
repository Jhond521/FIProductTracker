"""
Installment (cuota) amortization engine.

This is the core of the product's value proposition: given a purchase
amount, a monthly periodic rate, and a number of installments, compute
the fixed-payment (French/cuota fija) amortization schedule showing the
principal/interest split of each installment — the exact breakdown a
Colombian bank statement shows, but transparent to the user.

A monthly_rate of 0 models an interest-free promo purchase
("diferido sin intereses" / "N cuotas sin interés"): the payment is
simply principal / n_installments with zero interest in every period.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstallmentEntry:
    installment_number: int
    payment: float
    principal_portion: float
    interest_portion: float
    remaining_balance: float


def amortize_fixed_installments(
    principal: float,
    monthly_rate: float,
    n_installments: int,
) -> list[InstallmentEntry]:
    """Compute a fixed-payment amortization schedule.

    Uses the standard annuity formula for the payment amount when
    monthly_rate > 0:

        payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** -n)

    The final installment absorbs any rounding remainder so the schedule
    always fully amortizes the principal to exactly zero.
    """
    if principal <= 0:
        raise ValueError("principal must be positive")
    if n_installments <= 0:
        raise ValueError("n_installments must be a positive integer")
    if monthly_rate < 0:
        raise ValueError("monthly_rate cannot be negative")

    if monthly_rate == 0:
        base_payment = principal / n_installments
    else:
        base_payment = (
            principal * monthly_rate / (1 - (1 + monthly_rate) ** (-n_installments))
        )

    schedule: list[InstallmentEntry] = []
    balance = principal

    for i in range(1, n_installments + 1):
        interest_portion = balance * monthly_rate

        if i == n_installments:
            # Last installment: pay off whatever balance remains exactly,
            # rather than accumulating rounding drift.
            principal_portion = balance
        else:
            principal_portion = base_payment - interest_portion

        payment = principal_portion + interest_portion
        balance = balance - principal_portion

        schedule.append(
            InstallmentEntry(
                installment_number=i,
                payment=round(payment, 2),
                principal_portion=round(principal_portion, 2),
                interest_portion=round(interest_portion, 2),
                remaining_balance=round(max(balance, 0.0), 2),
            )
        )

    return schedule


def total_interest_cost(schedule: list[InstallmentEntry]) -> float:
    """Total interest paid across the whole schedule — the headline
    'real cost of credit' figure for a single purchase."""
    return round(sum(entry.interest_portion for entry in schedule), 2)


def real_annualized_cost(
    principal: float,
    schedule: list[InstallmentEntry],
) -> float:
    """Approximate the real annualized cost of a purchase as total
    interest paid relative to principal, annualized by the schedule's
    length in months. This is a simple approximation for the walking
    skeleton — refine to an IRR-based effective rate in a later pass
    once fees are integrated into the same calculation."""
    if not schedule:
        raise ValueError("schedule must not be empty")
    n_months = len(schedule)
    interest = total_interest_cost(schedule)
    return round((interest / principal) * (12 / n_months), 4)
