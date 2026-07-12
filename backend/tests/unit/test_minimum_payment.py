import pytest

from app.calculations.minimum_payment import (
    colombia_minimum_payment,
    us_minimum_payment,
)


def test_us_minimum_payment_percentage_leg_wins_on_large_balance():
    # 1% of 5000 + interest + fees (100) = 50 + 100 = 150, above the $25 floor
    result = us_minimum_payment(
        statement_balance=5000.0, period_interest=80.0, period_fees=20.0, flat_floor=25.0
    )
    assert result == pytest.approx(5000.0 * 0.01 + 80.0 + 20.0)


def test_us_minimum_payment_flat_floor_wins_on_small_balance():
    # 1% of 200 + 0 interest/fees = 2, well below the $25 floor
    result = us_minimum_payment(
        statement_balance=200.0, period_interest=0.0, period_fees=0.0, flat_floor=25.0
    )
    assert result == pytest.approx(25.0)


def test_us_minimum_payment_adds_past_due_amount_on_top():
    result = us_minimum_payment(
        statement_balance=200.0,
        period_interest=0.0,
        period_fees=0.0,
        past_due_amount=50.0,
        flat_floor=25.0,
    )
    assert result == pytest.approx(75.0)


def test_us_minimum_payment_default_floor_matches_prd_reference():
    # PRD Section 10 default MVP floor is $25 (Wells Fargo/BofA/Capital One shape)
    result = us_minimum_payment(statement_balance=0.0, period_interest=0.0, period_fees=0.0)
    assert result == pytest.approx(25.0)


def test_us_minimum_payment_negative_inputs_raise():
    with pytest.raises(ValueError):
        us_minimum_payment(statement_balance=-1.0, period_interest=0.0, period_fees=0.0)
    with pytest.raises(ValueError):
        us_minimum_payment(statement_balance=100.0, period_interest=0.0, period_fees=0.0, flat_floor=-1.0)


def test_colombia_minimum_payment_sums_period_cuotas_plus_fees():
    # CO's regulated minimum is already baked into each purchase's fixed
    # installment (cuota) — the period minimum is the sum of cuotas due
    # that period plus any recurring fee.
    result = colombia_minimum_payment(
        period_installment_payments=[45_000.0, 120_000.0], period_fees=15_000.0
    )
    assert result == pytest.approx(45_000.0 + 120_000.0 + 15_000.0)


def test_colombia_minimum_payment_no_purchases_due_is_just_fees():
    result = colombia_minimum_payment(period_installment_payments=[], period_fees=15_000.0)
    assert result == pytest.approx(15_000.0)
