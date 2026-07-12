"""
MarketRulesProfile — the strategy abstraction described in PRD Section 5.

Colombia and US credit cards differ structurally, not just in field values
(per-purchase installment accrual vs. single revolving APR against an
average daily balance), so `calculations/` must never branch "if Colombia"
inline. Instead each market gets its own MarketRulesProfile implementation
for interest calculation, minimum-payment formula, and grace-period rule;
callers select the right one via `get_market_rules(product.market)`.

Adding a third market later means adding one more MarketRulesProfile
subclass, not touching the two that already exist.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.calculations.amortization import InstallmentEntry, amortize_fixed_installments
from app.calculations.average_daily_balance import adb_interest_charge
from app.calculations.minimum_payment import (
    US_DEFAULT_FLAT_FLOOR,
    colombia_minimum_payment,
    us_minimum_payment,
)
from app.calculations.rates import ea_to_monthly_rate

VALID_MARKETS = ("CO", "US")


class MarketRulesProfile(ABC):
    """One interface, selected by market, for the three things that differ
    structurally between markets (PRD Section 5). The two markets' inputs
    are genuinely different shapes (installment terms vs. a billing-cycle
    balance), so each implementation takes market-appropriate keyword
    arguments rather than forcing a false shared signature.
    """

    market: str

    @abstractmethod
    def compute_interest(self, **kwargs):
        """Interest for this market's unit of calculation."""

    @abstractmethod
    def compute_minimum_payment(self, **kwargs) -> float:
        """This market's minimum-payment formula."""

    @abstractmethod
    def grace_period_waives_interest(self, **kwargs) -> bool:
        """Whether this market's grace-period condition is currently met."""


class ColombiaMarketRules(MarketRulesProfile):
    market = "CO"

    def compute_interest(
        self,
        *,
        principal: float,
        ea_rate: float,
        n_installments: int,
        interest_free_promo: bool = False,
    ) -> list[InstallmentEntry]:
        """Per-purchase fixed-installment (cuota fija) amortization schedule,
        derived from the product's disclosed EA rate."""
        monthly_rate = 0.0 if interest_free_promo else ea_to_monthly_rate(ea_rate)
        return amortize_fixed_installments(
            principal=principal, monthly_rate=monthly_rate, n_installments=n_installments
        )

    def compute_minimum_payment(
        self, *, period_installment_payments: list[float], period_fees: float = 0.0
    ) -> float:
        return colombia_minimum_payment(period_installment_payments, period_fees)

    def grace_period_waives_interest(self, *, statement_paid_in_full: bool) -> bool:
        """"Pago total": paying the full statement balance waives interest
        for that period."""
        return statement_paid_in_full


class USMarketRules(MarketRulesProfile):
    market = "US"

    def compute_interest(
        self,
        *,
        average_daily_balance_amount: float,
        apr: float,
        day_count_basis: int,
        days_in_cycle: int,
        grace_period_waived: bool = False,
    ) -> float:
        """Single revolving charge for the billing cycle, via the
        average-daily-balance method against the disclosed APR."""
        if grace_period_waived:
            return 0.0
        return adb_interest_charge(average_daily_balance_amount, apr, day_count_basis, days_in_cycle)

    def compute_minimum_payment(
        self,
        *,
        statement_balance: float,
        period_interest: float,
        period_fees: float,
        past_due_amount: float = 0.0,
        flat_floor: float = US_DEFAULT_FLAT_FLOOR,
    ) -> float:
        return us_minimum_payment(
            statement_balance=statement_balance,
            period_interest=period_interest,
            period_fees=period_fees,
            past_due_amount=past_due_amount,
            flat_floor=flat_floor,
        )

    def grace_period_waives_interest(self, *, previous_statement_paid_in_full: bool) -> bool:
        """US grace period is a whole-account condition: new purchases are
        interest-free only if the *previous* statement was paid in full by
        its due date -- not a per-purchase condition like Colombia's."""
        return previous_statement_paid_in_full


_PROFILES: dict[str, type[MarketRulesProfile]] = {
    "CO": ColombiaMarketRules,
    "US": USMarketRules,
}


def get_market_rules(market: str) -> MarketRulesProfile:
    """Select the MarketRulesProfile for a FinancialProduct.market value."""
    try:
        return _PROFILES[market]()
    except KeyError:
        raise ValueError(f"Unknown market {market!r}; expected one of {VALID_MARKETS}") from None
