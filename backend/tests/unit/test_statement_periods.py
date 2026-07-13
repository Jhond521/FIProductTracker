import uuid
from datetime import date

import pytest

from app.calculations.statement_periods import (
    PeriodPurchaseInput,
    build_co_period_statement,
    build_us_period_statement,
    list_statement_periods,
    outstanding_balance,
    period_shifted,
    statement_period_containing,
)


def test_purchase_on_cutoff_day_lands_in_that_periods_close():
    period = statement_period_containing(date(2026, 3, 15), cutoff_day=15, payment_due_day=5)
    assert period.period_start == date(2026, 2, 16)
    assert period.period_end == date(2026, 3, 15)


def test_purchase_after_cutoff_lands_in_next_period():
    period = statement_period_containing(date(2026, 3, 16), cutoff_day=15, payment_due_day=5)
    assert period.period_start == date(2026, 3, 16)
    assert period.period_end == date(2026, 4, 15)


def test_due_date_rolls_to_next_month_when_due_day_before_cutoff_day():
    period = statement_period_containing(date(2026, 3, 1), cutoff_day=15, payment_due_day=5)
    assert period.period_end == date(2026, 3, 15)
    assert period.due_date == date(2026, 4, 5)


def test_due_date_stays_same_month_when_due_day_after_cutoff_day():
    period = statement_period_containing(date(2026, 3, 1), cutoff_day=5, payment_due_day=20)
    assert period.period_end == date(2026, 3, 5)
    assert period.due_date == date(2026, 3, 20)


def test_period_shifted_advances_by_whole_cycles():
    first = statement_period_containing(date(2026, 1, 20), cutoff_day=15, payment_due_day=5)
    later = period_shifted(first, 3, cutoff_day=15, payment_due_day=5)
    assert later.period_end == date(2026, 5, 15)
    assert later.period_start == date(2026, 4, 16)


def test_period_boundary_spans_year_end():
    period = statement_period_containing(date(2026, 1, 5), cutoff_day=15, payment_due_day=5)
    assert period.period_start == date(2025, 12, 16)
    assert period.period_end == date(2026, 1, 15)


class TestCoPeriodStatement:
    def test_single_installment_purchase_contributes_full_amount(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=300_000.0,
            purchase_date=date(2026, 3, 1),
            n_installments=1,
            interest_free_promo=True,
        )
        statement = build_co_period_statement(
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            purchases=[purchase],
            target_period_end=date(2026, 3, 15),
        )
        assert len(statement.contributions) == 1
        assert statement.contributions[0].principal_portion == pytest.approx(300_000.0)
        assert statement.total_interest == pytest.approx(0.0)
        assert statement.total_due == pytest.approx(300_000.0)

    def test_purchase_after_cutoff_does_not_contribute_to_that_periods_close(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=100_000.0,
            purchase_date=date(2026, 3, 16),  # one day after cutoff
            n_installments=1,
        )
        statement = build_co_period_statement(
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            purchases=[purchase],
            target_period_end=date(2026, 3, 15),
        )
        assert statement.contributions == []
        assert statement.total_due == 0.0

    def test_installments_spread_across_consecutive_periods(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=600_000.0,
            purchase_date=date(2026, 3, 1),
            n_installments=3,
        )
        first = build_co_period_statement(
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            purchases=[purchase],
            target_period_end=date(2026, 3, 15),
        )
        second = build_co_period_statement(
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            purchases=[purchase],
            target_period_end=date(2026, 4, 15),
        )
        third = build_co_period_statement(
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            purchases=[purchase],
            target_period_end=date(2026, 5, 15),
        )
        assert len(first.contributions) == 1
        assert len(second.contributions) == 1
        assert len(third.contributions) == 1

        # Principal across all three installments reconciles to the original purchase amount
        total_principal = (
            first.total_principal + second.total_principal + third.total_principal
        )
        assert total_principal == pytest.approx(600_000.0, rel=1e-6)

    def test_multiple_purchases_in_same_period_are_all_included(self):
        purchases = [
            PeriodPurchaseInput(
                purchase_id=uuid.uuid4(),
                amount=100_000.0,
                purchase_date=date(2026, 3, 1),
                n_installments=1,
                interest_free_promo=True,
            ),
            PeriodPurchaseInput(
                purchase_id=uuid.uuid4(),
                amount=50_000.0,
                purchase_date=date(2026, 3, 10),
                n_installments=1,
                interest_free_promo=True,
            ),
        ]
        statement = build_co_period_statement(
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            purchases=purchases,
            target_period_end=date(2026, 3, 15),
        )
        assert len(statement.contributions) == 2
        assert statement.total_principal == pytest.approx(150_000.0)


class TestUsPeriodStatement:
    def test_new_purchase_within_period_contributes_principal_and_accrues_interest(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=1_000.0,
            purchase_date=date(2026, 3, 1),
            n_installments=1,
        )
        statement = build_us_period_statement(
            cutoff_day=15,
            payment_due_day=5,
            apr=0.24,
            day_count_basis=365,
            purchases=[purchase],
            target_period_end=date(2026, 3, 15),
        )
        assert len(statement.contributions) == 1
        assert statement.total_principal == pytest.approx(1_000.0)
        assert statement.total_interest > 0
        assert statement.total_due == pytest.approx(
            statement.total_principal + statement.total_interest
        )

    def test_balance_carries_into_next_cycle_and_keeps_accruing_interest(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=1_000.0,
            purchase_date=date(2026, 2, 1),
            n_installments=1,
        )
        next_cycle = build_us_period_statement(
            cutoff_day=15,
            payment_due_day=5,
            apr=0.24,
            day_count_basis=365,
            purchases=[purchase],
            target_period_end=date(2026, 3, 15),
        )
        # No payment tracking yet, so the purchase isn't a "new" contribution
        # in the following cycle, but its balance still accrues interest.
        assert next_cycle.contributions == []
        assert next_cycle.total_interest > 0

    def test_purchase_after_cutoff_excluded_from_that_cycles_new_principal(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=1_000.0,
            purchase_date=date(2026, 3, 16),
            n_installments=1,
        )
        statement = build_us_period_statement(
            cutoff_day=15,
            payment_due_day=5,
            apr=0.24,
            day_count_basis=365,
            purchases=[purchase],
            target_period_end=date(2026, 3, 15),
        )
        assert statement.contributions == []
        assert statement.total_interest == pytest.approx(0.0)


class TestListStatementPeriods:
    def test_empty_purchases_returns_empty_list(self):
        assert (
            list_statement_periods(
                market="CO",
                cutoff_day=15,
                payment_due_day=5,
                ea_rate=0.36,
                apr=None,
                day_count_basis=365,
                purchases=[],
                as_of=date(2026, 6, 1),
            )
            == []
        )

    def test_co_lists_one_period_per_installment_newest_first(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=300_000.0,
            purchase_date=date(2026, 1, 10),
            n_installments=3,
        )
        periods = list_statement_periods(
            market="CO",
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            apr=None,
            day_count_basis=365,
            purchases=[purchase],
            as_of=date(2026, 6, 1),
        )
        assert [p.period_end for p in periods] == [
            date(2026, 3, 15),
            date(2026, 2, 15),
            date(2026, 1, 15),
        ]

    def test_us_lists_a_period_for_every_cycle_the_balance_is_outstanding(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=1_000.0,
            purchase_date=date(2026, 1, 10),
            n_installments=1,
        )
        periods = list_statement_periods(
            market="US",
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=None,
            apr=0.24,
            day_count_basis=365,
            purchases=[purchase],
            as_of=date(2026, 3, 20),
        )
        # Balance never paid off (no payment tracking), so it keeps
        # appearing (with accruing interest) through the current period.
        assert [p.period_end for p in periods] == [
            date(2026, 4, 15),
            date(2026, 3, 15),
            date(2026, 2, 15),
            date(2026, 1, 15),
        ]


class TestOutstandingBalance:
    def test_co_balance_before_first_installment_closes_is_full_amount(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=300_000.0,
            purchase_date=date(2026, 3, 10),
            n_installments=3,
        )
        balance = outstanding_balance(
            market="CO",
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            purchases=[purchase],
            as_of=date(2026, 3, 12),  # before the first period even closes
        )
        assert balance == pytest.approx(300_000.0)

    def test_co_balance_shrinks_as_installments_close(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=300_000.0,
            purchase_date=date(2026, 3, 10),
            n_installments=3,
        )
        after_one = outstanding_balance(
            market="CO",
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            purchases=[purchase],
            as_of=date(2026, 3, 20),  # first installment period (Mar 15) has closed
        )
        after_two = outstanding_balance(
            market="CO",
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            purchases=[purchase],
            as_of=date(2026, 4, 20),
        )
        after_all = outstanding_balance(
            market="CO",
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            purchases=[purchase],
            as_of=date(2026, 5, 20),
        )
        assert after_one > after_two > after_all
        assert after_all == 0.0

    def test_co_balance_sums_across_multiple_purchases(self):
        purchases = [
            PeriodPurchaseInput(
                purchase_id=uuid.uuid4(),
                amount=100_000.0,
                purchase_date=date(2026, 3, 1),
                n_installments=1,
                interest_free_promo=True,
            ),
            PeriodPurchaseInput(
                purchase_id=uuid.uuid4(),
                amount=50_000.0,
                purchase_date=date(2026, 3, 1),
                n_installments=1,
                interest_free_promo=True,
            ),
        ]
        balance = outstanding_balance(
            market="CO",
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=0.36,
            purchases=purchases,
            as_of=date(2026, 3, 10),  # before cutoff, nothing billed yet
        )
        assert balance == pytest.approx(150_000.0)

    def test_us_balance_is_sum_of_purchases_to_date(self):
        purchases = [
            PeriodPurchaseInput(
                purchase_id=uuid.uuid4(),
                amount=1_000.0,
                purchase_date=date(2026, 2, 1),
                n_installments=1,
            ),
            PeriodPurchaseInput(
                purchase_id=uuid.uuid4(),
                amount=500.0,
                purchase_date=date(2026, 3, 1),
                n_installments=1,
            ),
        ]
        balance = outstanding_balance(
            market="US",
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=None,
            purchases=purchases,
            as_of=date(2026, 3, 20),
        )
        assert balance == pytest.approx(1_500.0)

    def test_us_balance_excludes_purchases_after_as_of(self):
        purchases = [
            PeriodPurchaseInput(
                purchase_id=uuid.uuid4(),
                amount=1_000.0,
                purchase_date=date(2026, 4, 1),
                n_installments=1,
            ),
        ]
        balance = outstanding_balance(
            market="US",
            cutoff_day=15,
            payment_due_day=5,
            ea_rate=None,
            purchases=purchases,
            as_of=date(2026, 3, 20),
        )
        assert balance == 0.0

    def test_no_purchases_is_zero_balance(self):
        assert (
            outstanding_balance(
                market="CO",
                cutoff_day=15,
                payment_due_day=5,
                ea_rate=0.36,
                purchases=[],
                as_of=date(2026, 3, 20),
            )
            == 0.0
        )
