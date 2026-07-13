import uuid
from datetime import date

import pytest

from app.calculations.recommendations import (
    RecommendationProductInput,
    UTILIZATION_RISK_THRESHOLD,
    build_recommendations,
)
from app.calculations.statement_periods import PeriodPurchaseInput


def make_co_product(*, purchases, ea_rate=0.36, credit_limit=5_000_000.0, **overrides) -> RecommendationProductInput:
    defaults = dict(
        product_id=uuid.uuid4(),
        institution_name="Banco de Prueba",
        market="CO",
        credit_limit=credit_limit,
        ea_rate=ea_rate,
        apr=None,
        day_count_basis=365,
        cutoff_day=15,
        payment_due_day=5,
        min_payment_flat_floor=None,
        purchases=purchases,
    )
    defaults.update(overrides)
    return RecommendationProductInput(**defaults)


def make_us_product(*, purchases, apr=0.24, credit_limit=10_000.0, **overrides) -> RecommendationProductInput:
    defaults = dict(
        product_id=uuid.uuid4(),
        institution_name="Chase",
        market="US",
        credit_limit=credit_limit,
        ea_rate=None,
        apr=apr,
        day_count_basis=365,
        cutoff_day=15,
        payment_due_day=5,
        min_payment_flat_floor=None,
        purchases=purchases,
    )
    defaults.update(overrides)
    return RecommendationProductInput(**defaults)


class TestRealCostExceedsRate:
    def test_normal_purchase_not_flagged_under_current_approximation(self):
        """real_annualized_cost is a simple linear annualization (see its
        docstring) that's mathematically always <= the compounded EA it's
        derived from, so a plain non-promo purchase never trips this flag
        today -- this documents that invariant rather than a false
        positive. The comparison itself is still correct and will start
        firing once the underlying cost calculation is refined (e.g. to
        an IRR-based rate) or per-purchase fees are wired in."""
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=100_000.0,
            purchase_date=date(2026, 3, 1),
            n_installments=6,
        )
        product = make_co_product(purchases=[purchase], ea_rate=0.36)
        recs = build_recommendations([product], as_of=date(2026, 3, 1))
        assert recs.real_cost_exceeds_rate == []

    def test_interest_free_promo_never_flagged(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=100_000.0,
            purchase_date=date(2026, 3, 1),
            n_installments=1,
            interest_free_promo=True,
        )
        product = make_co_product(purchases=[purchase])
        recs = build_recommendations([product], as_of=date(2026, 3, 1))
        assert recs.real_cost_exceeds_rate == []

    def test_us_purchases_never_flagged(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(), amount=500.0, purchase_date=date(2026, 3, 1), n_installments=1
        )
        product = make_us_product(purchases=[purchase])
        recs = build_recommendations([product], as_of=date(2026, 3, 1))
        assert recs.real_cost_exceeds_rate == []


class TestPayInFullSavesInterest:
    def test_us_card_with_interest_this_cycle_is_flagged(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(), amount=1_000.0, purchase_date=date(2026, 3, 1), n_installments=1
        )
        product = make_us_product(purchases=[purchase])
        recs = build_recommendations([product], as_of=date(2026, 3, 20))
        assert len(recs.pay_in_full_saves_interest) == 1
        flag = recs.pay_in_full_saves_interest[0]
        assert flag.current_period_interest > 0
        assert flag.statement_balance == pytest.approx(1_000.0)
        assert flag.minimum_payment > 0

    def test_us_card_with_no_purchases_is_not_flagged(self):
        product = make_us_product(purchases=[])
        recs = build_recommendations([product], as_of=date(2026, 3, 20))
        assert recs.pay_in_full_saves_interest == []

    def test_co_card_never_flagged(self):
        """CO's cuotas are fixed at purchase time -- paying extra doesn't
        change interest already baked into the schedule, so this flag
        doesn't apply to CO in this model."""
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=300_000.0,
            purchase_date=date(2026, 3, 1),
            n_installments=3,
        )
        product = make_co_product(purchases=[purchase])
        recs = build_recommendations([product], as_of=date(2026, 3, 20))
        assert recs.pay_in_full_saves_interest == []


class TestPromoExpiring:
    def test_promo_on_last_installment_is_flagged(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=300_000.0,
            purchase_date=date(2026, 1, 1),
            n_installments=3,
            interest_free_promo=True,
        )
        product = make_co_product(purchases=[purchase])
        # First period Jan 15, second Feb 15, third Mar 15 -- as_of Mar 1
        # means 2 installments elapsed, 1 remaining.
        recs = build_recommendations([product], as_of=date(2026, 3, 1))
        assert len(recs.promo_expiring) == 1
        flag = recs.promo_expiring[0]
        assert flag.purchase_id == purchase.purchase_id
        assert flag.installments_remaining == 1

    def test_promo_early_in_schedule_not_flagged(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=300_000.0,
            purchase_date=date(2026, 1, 1),
            n_installments=6,
            interest_free_promo=True,
        )
        product = make_co_product(purchases=[purchase])
        recs = build_recommendations([product], as_of=date(2026, 1, 5))
        assert recs.promo_expiring == []

    def test_completed_promo_not_flagged(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=300_000.0,
            purchase_date=date(2026, 1, 1),
            n_installments=3,
            interest_free_promo=True,
        )
        product = make_co_product(purchases=[purchase])
        recs = build_recommendations([product], as_of=date(2026, 4, 1))
        assert recs.promo_expiring == []

    def test_non_promo_purchase_never_flagged(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=300_000.0,
            purchase_date=date(2026, 1, 1),
            n_installments=3,
            interest_free_promo=False,
        )
        product = make_co_product(purchases=[purchase])
        recs = build_recommendations([product], as_of=date(2026, 3, 1))
        assert recs.promo_expiring == []

    def test_us_never_flagged(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(),
            amount=1_000.0,
            purchase_date=date(2026, 1, 1),
            n_installments=1,
        )
        product = make_us_product(purchases=[purchase])
        recs = build_recommendations([product], as_of=date(2026, 3, 1))
        assert recs.promo_expiring == []


class TestAvalanchePayoffOrder:
    def test_ranks_by_disclosed_rate_descending_across_markets(self):
        co_purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(), amount=300_000.0, purchase_date=date(2026, 3, 1), n_installments=1
        )
        us_purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(), amount=500.0, purchase_date=date(2026, 3, 1), n_installments=1
        )
        co_product = make_co_product(purchases=[co_purchase], ea_rate=0.20)
        us_product = make_us_product(purchases=[us_purchase], apr=0.29)

        recs = build_recommendations([co_product, us_product], as_of=date(2026, 3, 1))
        assert [e.product_id for e in recs.avalanche_payoff_order] == [
            us_product.product_id,
            co_product.product_id,
        ]

    def test_cards_with_zero_balance_excluded(self):
        product = make_co_product(purchases=[])
        recs = build_recommendations([product], as_of=date(2026, 3, 1))
        assert recs.avalanche_payoff_order == []


class TestUtilizationRisk:
    def test_high_utilization_flagged(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(), amount=4_000_000.0, purchase_date=date(2026, 3, 1), n_installments=1
        )
        product = make_co_product(purchases=[purchase], credit_limit=5_000_000.0)
        recs = build_recommendations([product], as_of=date(2026, 3, 1))
        assert len(recs.utilization_risk) == 1
        flag = recs.utilization_risk[0]
        assert flag.utilization == pytest.approx(0.8)
        assert flag.threshold == UTILIZATION_RISK_THRESHOLD

    def test_low_utilization_not_flagged(self):
        purchase = PeriodPurchaseInput(
            purchase_id=uuid.uuid4(), amount=100_000.0, purchase_date=date(2026, 3, 1), n_installments=1
        )
        product = make_co_product(purchases=[purchase], credit_limit=5_000_000.0)
        recs = build_recommendations([product], as_of=date(2026, 3, 1))
        assert recs.utilization_risk == []

    def test_no_purchases_not_flagged(self):
        product = make_co_product(purchases=[])
        recs = build_recommendations([product], as_of=date(2026, 3, 1))
        assert recs.utilization_risk == []


def test_no_products_returns_empty_recommendation_set():
    recs = build_recommendations([], as_of=date(2026, 3, 1))
    assert recs.real_cost_exceeds_rate == []
    assert recs.pay_in_full_saves_interest == []
    assert recs.promo_expiring == []
    assert recs.avalanche_payoff_order == []
    assert recs.utilization_risk == []
