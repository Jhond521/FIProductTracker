import pytest

from app.calculations.average_daily_balance import (
    adb_interest_charge,
    apr_to_daily_rate,
    average_daily_balance,
)


def test_average_daily_balance_of_flat_balance_is_that_balance():
    assert average_daily_balance([1000.0] * 30) == pytest.approx(1000.0)


def test_average_daily_balance_weights_each_day_equally():
    # 10 days at 100, 20 days at 400 -> (10*100 + 20*400) / 30
    balances = [100.0] * 10 + [400.0] * 20
    expected = (10 * 100.0 + 20 * 400.0) / 30
    assert average_daily_balance(balances) == pytest.approx(expected)


def test_average_daily_balance_empty_raises():
    with pytest.raises(ValueError):
        average_daily_balance([])


def test_apr_to_daily_rate_is_simple_division_not_geometric():
    # APR is a nominal rate: US convention divides linearly by the
    # day-count basis, unlike Colombia's EA geometric conversion.
    assert apr_to_daily_rate(0.24, 365) == pytest.approx(0.24 / 365)
    assert apr_to_daily_rate(0.24, 360) == pytest.approx(0.24 / 360)


def test_apr_to_daily_rate_invalid_basis_raises():
    with pytest.raises(ValueError):
        apr_to_daily_rate(0.24, 366)


def test_adb_interest_charge_known_value():
    # $1000 average daily balance, 24% APR, 365 day-count, 30-day cycle
    avg_balance = 1000.0
    apr = 0.24
    day_count_basis = 365
    days_in_cycle = 30
    expected = avg_balance * (apr / day_count_basis) * days_in_cycle
    assert adb_interest_charge(avg_balance, apr, day_count_basis, days_in_cycle) == pytest.approx(
        round(expected, 2)
    )


def test_adb_interest_charge_zero_balance_is_zero():
    assert adb_interest_charge(0.0, 0.24, 365, 30) == 0.0


def test_adb_interest_charge_negative_apr_raises():
    with pytest.raises(ValueError):
        adb_interest_charge(1000.0, -0.01, 365, 30)


def test_adb_interest_charge_negative_balance_raises():
    with pytest.raises(ValueError):
        adb_interest_charge(-100.0, 0.24, 365, 30)
