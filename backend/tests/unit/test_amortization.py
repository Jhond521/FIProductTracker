import pytest

from app.calculations.amortization import (
    amortize_fixed_installments,
    real_annualized_cost,
    total_interest_cost,
)
from app.calculations.rates import ea_to_monthly_rate


def test_zero_rate_installments_split_evenly_no_interest():
    schedule = amortize_fixed_installments(principal=1200.0, monthly_rate=0.0, n_installments=12)

    assert len(schedule) == 12
    assert all(entry.interest_portion == 0.0 for entry in schedule)
    assert sum(entry.principal_portion for entry in schedule) == pytest.approx(1200.0)
    assert schedule[-1].remaining_balance == 0.0


def test_schedule_fully_amortizes_to_zero_with_interest():
    monthly_rate = ea_to_monthly_rate(0.36)  # a realistic CC EA
    schedule = amortize_fixed_installments(principal=1_000_000.0, monthly_rate=monthly_rate, n_installments=6)

    assert schedule[-1].remaining_balance == 0.0
    # Sum of principal portions must reconstruct the original principal
    assert sum(e.principal_portion for e in schedule) == pytest.approx(1_000_000.0, rel=1e-6)


def test_interest_portion_decreases_over_time_with_positive_rate():
    monthly_rate = ea_to_monthly_rate(0.36)
    schedule = amortize_fixed_installments(principal=500_000.0, monthly_rate=monthly_rate, n_installments=9)

    interest_amounts = [e.interest_portion for e in schedule]
    # Interest should be monotonically non-increasing as balance shrinks
    assert all(earlier >= later for earlier, later in zip(interest_amounts, interest_amounts[1:]))


def test_single_installment_equals_principal_plus_one_period_interest():
    monthly_rate = 0.02
    schedule = amortize_fixed_installments(principal=100_000.0, monthly_rate=monthly_rate, n_installments=1)

    assert len(schedule) == 1
    assert schedule[0].interest_portion == pytest.approx(2_000.0)
    assert schedule[0].principal_portion == pytest.approx(100_000.0)
    assert schedule[0].remaining_balance == 0.0


def test_total_interest_cost_matches_manual_sum():
    monthly_rate = ea_to_monthly_rate(0.45)
    schedule = amortize_fixed_installments(principal=800_000.0, monthly_rate=monthly_rate, n_installments=3)

    manual_sum = round(sum(e.interest_portion for e in schedule), 2)
    assert total_interest_cost(schedule) == manual_sum


def test_real_annualized_cost_zero_for_interest_free_promo():
    schedule = amortize_fixed_installments(principal=300_000.0, monthly_rate=0.0, n_installments=6)
    assert real_annualized_cost(300_000.0, schedule) == pytest.approx(0.0)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        amortize_fixed_installments(principal=0, monthly_rate=0.02, n_installments=6)
    with pytest.raises(ValueError):
        amortize_fixed_installments(principal=100, monthly_rate=0.02, n_installments=0)
    with pytest.raises(ValueError):
        amortize_fixed_installments(principal=100, monthly_rate=-0.01, n_installments=3)
