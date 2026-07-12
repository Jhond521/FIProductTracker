import pytest

from app.calculations.average_daily_balance import adb_interest_charge
from app.calculations.market_rules import (
    ColombiaMarketRules,
    USMarketRules,
    get_market_rules,
)
from app.calculations.rates import ea_to_monthly_rate


def test_get_market_rules_returns_correct_profile():
    assert isinstance(get_market_rules("CO"), ColombiaMarketRules)
    assert isinstance(get_market_rules("US"), USMarketRules)


def test_get_market_rules_unknown_market_raises():
    with pytest.raises(ValueError):
        get_market_rules("MX")


def test_colombia_compute_interest_matches_amortization_engine_directly():
    rules = ColombiaMarketRules()
    schedule = rules.compute_interest(
        principal=1_000_000.0, ea_rate=0.36, n_installments=6, interest_free_promo=False
    )
    monthly_rate = ea_to_monthly_rate(0.36)
    assert schedule[0].interest_portion == pytest.approx(1_000_000.0 * monthly_rate, rel=1e-6)
    assert schedule[-1].remaining_balance == 0.0


def test_colombia_interest_free_promo_yields_zero_interest():
    rules = ColombiaMarketRules()
    schedule = rules.compute_interest(
        principal=300_000.0, ea_rate=0.36, n_installments=6, interest_free_promo=True
    )
    assert all(entry.interest_portion == 0.0 for entry in schedule)


def test_colombia_minimum_payment_and_grace_period_are_independent_of_us():
    rules = ColombiaMarketRules()
    assert rules.compute_minimum_payment(
        period_installment_payments=[50_000.0], period_fees=10_000.0
    ) == pytest.approx(60_000.0)
    assert rules.grace_period_waives_interest(statement_paid_in_full=True) is True
    assert rules.grace_period_waives_interest(statement_paid_in_full=False) is False


def test_us_compute_interest_matches_adb_engine_directly():
    rules = USMarketRules()
    result = rules.compute_interest(
        average_daily_balance_amount=2_000.0, apr=0.22, day_count_basis=365, days_in_cycle=30
    )
    expected = adb_interest_charge(2_000.0, 0.22, 365, 30)
    assert result == pytest.approx(expected)


def test_us_grace_period_waives_all_interest_for_the_cycle():
    rules = USMarketRules()
    result = rules.compute_interest(
        average_daily_balance_amount=2_000.0,
        apr=0.22,
        day_count_basis=365,
        days_in_cycle=30,
        grace_period_waived=True,
    )
    assert result == 0.0


def test_us_grace_period_condition_is_previous_cycle_not_current():
    rules = USMarketRules()
    assert rules.grace_period_waives_interest(previous_statement_paid_in_full=True) is True
    assert rules.grace_period_waives_interest(previous_statement_paid_in_full=False) is False


def test_us_minimum_payment_delegates_to_reference_formula():
    rules = USMarketRules()
    result = rules.compute_minimum_payment(
        statement_balance=5000.0, period_interest=80.0, period_fees=20.0, flat_floor=25.0
    )
    assert result == pytest.approx(5000.0 * 0.01 + 80.0 + 20.0)


def test_colombia_and_us_engines_reconcile_independently_same_principal():
    # Same nominal principal/rate fed through both markets must not leak
    # any behavior between the two -- CO amortizes to a schedule, US
    # produces a single cycle charge, and neither should equal the other's
    # shape or default.
    co_rules = ColombiaMarketRules()
    us_rules = USMarketRules()

    co_schedule = co_rules.compute_interest(principal=1000.0, ea_rate=0.24, n_installments=12)
    us_charge = us_rules.compute_interest(
        average_daily_balance_amount=1000.0, apr=0.24, day_count_basis=365, days_in_cycle=30
    )

    assert isinstance(co_schedule, list)
    assert isinstance(us_charge, float)
    assert sum(e.principal_portion for e in co_schedule) == pytest.approx(1000.0)
