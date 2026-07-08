import pytest

from app.calculations.rates import (
    ea_to_daily_rate,
    ea_to_monthly_rate,
    ea_to_periodic_rate,
)


def test_ea_to_periodic_rate_zero_ea_is_zero():
    assert ea_to_periodic_rate(0.0, 365) == pytest.approx(0.0)


def test_ea_to_daily_rate_known_value():
    # 30% EA -> daily rate over 365 days
    # (1.30)^(1/365) - 1
    ea = 0.30
    expected = (1 + ea) ** (1 / 365) - 1
    assert ea_to_daily_rate(ea, 365) == pytest.approx(expected)


def test_ea_to_daily_rate_360_vs_365_differ():
    ea = 0.30
    rate_360 = ea_to_daily_rate(ea, 360)
    rate_365 = ea_to_daily_rate(ea, 365)
    # Same EA, fewer compounding days in the year -> higher daily rate
    assert rate_360 > rate_365


def test_ea_to_daily_rate_invalid_basis_raises():
    with pytest.raises(ValueError):
        ea_to_daily_rate(0.30, 366)


def test_ea_to_daily_rate_compounds_back_to_ea():
    # Compounding the daily rate for a full year should reconstruct EA
    ea = 0.4576  # a realistic Colombian credit card EA
    daily = ea_to_daily_rate(ea, 365)
    reconstructed = (1 + daily) ** 365 - 1
    assert reconstructed == pytest.approx(ea, rel=1e-9)


def test_ea_to_monthly_rate_compounds_back_to_ea():
    ea = 0.36
    monthly = ea_to_monthly_rate(ea)
    reconstructed = (1 + monthly) ** 12 - 1
    assert reconstructed == pytest.approx(ea, rel=1e-9)


def test_negative_ea_below_limit_raises():
    with pytest.raises(ValueError):
        ea_to_periodic_rate(-1.5, 365)
