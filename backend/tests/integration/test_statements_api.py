import uuid

import pytest

pytestmark = pytest.mark.anyio


async def test_co_statement_periods_list_and_drill_down(authenticated_client):
    product_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 5_000_000.0,
            "ea_rate": 0.36,
            "day_count_basis": 365,
            "statement_cutoff_day": 15,
            "payment_due_day": 5,
        },
    )
    assert product_resp.status_code == 201
    product = product_resp.json()
    assert product["statement_cutoff_day"] == 15
    assert product["payment_due_day"] == 5

    purchase_resp = await authenticated_client.post(
        f"/api/v1/internal/products/{product['id']}/purchases",
        json={
            "amount": 300_000.0,
            "currency": "COP",
            "purchase_date": "2026-03-01",
            "n_installments": 3,
            "description": "Electrodomestico",
        },
    )
    assert purchase_resp.status_code == 201
    purchase = purchase_resp.json()

    list_resp = await authenticated_client.get(f"/api/v1/internal/products/{product['id']}/statements")
    assert list_resp.status_code == 200
    periods = list_resp.json()
    assert [p["period_end"] for p in periods] == ["2026-05-15", "2026-04-15", "2026-03-15"]
    assert all(p["total_due"] > 0 for p in periods)

    detail_resp = await authenticated_client.get(
        f"/api/v1/internal/products/{product['id']}/statements/2026-03-15"
    )
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["contributions"]) == 1
    assert detail["contributions"][0]["purchase_id"] == purchase["id"]
    assert detail["contributions"][0]["description"] == "Electrodomestico"
    assert detail["total_due"] == pytest.approx(
        detail["total_principal"] + detail["total_interest"]
    )

    # Principal across all three drill-down periods reconciles to the purchase amount
    total_principal = 0.0
    for period_end in ("2026-03-15", "2026-04-15", "2026-05-15"):
        resp = await authenticated_client.get(
            f"/api/v1/internal/products/{product['id']}/statements/{period_end}"
        )
        total_principal += resp.json()["total_principal"]
    assert total_principal == pytest.approx(300_000.0, rel=1e-6)


async def test_purchase_after_cutoff_lands_in_next_statement_period(authenticated_client):
    product_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 5_000_000.0,
            "ea_rate": 0.36,
            "day_count_basis": 365,
            "statement_cutoff_day": 15,
            "payment_due_day": 5,
        },
    )
    product = product_resp.json()

    await authenticated_client.post(
        f"/api/v1/internal/products/{product['id']}/purchases",
        json={
            "amount": 100_000.0,
            "currency": "COP",
            "purchase_date": "2026-03-16",  # one day after cutoff
            "n_installments": 1,
            "interest_free_promo": True,
        },
    )

    same_month_resp = await authenticated_client.get(
        f"/api/v1/internal/products/{product['id']}/statements/2026-03-15"
    )
    assert same_month_resp.status_code == 404

    next_period_resp = await authenticated_client.get(
        f"/api/v1/internal/products/{product['id']}/statements/2026-04-15"
    )
    assert next_period_resp.status_code == 200
    assert next_period_resp.json()["total_principal"] == pytest.approx(100_000.0)


async def test_us_statement_period_carries_balance_and_accrues_interest(authenticated_client):
    product_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "US",
            "institution_name": "Chase",
            "credit_limit": 10_000.0,
            "day_count_basis": 365,
            "apr": 0.24,
            "statement_cutoff_day": 15,
            "payment_due_day": 5,
        },
    )
    product = product_resp.json()

    await authenticated_client.post(
        f"/api/v1/internal/products/{product['id']}/purchases",
        json={
            "amount": 1_000.0,
            "currency": "USD",
            "purchase_date": "2026-02-01",
        },
    )

    list_resp = await authenticated_client.get(f"/api/v1/internal/products/{product['id']}/statements")
    assert list_resp.status_code == 200
    periods = {p["period_end"]: p for p in list_resp.json()}
    assert "2026-02-15" in periods
    assert "2026-03-15" in periods  # balance carries even without a new purchase
    assert periods["2026-02-15"]["total_principal"] == pytest.approx(1_000.0)
    assert periods["2026-03-15"]["total_principal"] == pytest.approx(0.0)
    assert periods["2026-03-15"]["total_interest"] > 0


async def test_statements_require_authentication(async_client):
    resp = await async_client.get(f"/api/v1/internal/products/{uuid.uuid4()}/statements")
    assert resp.status_code == 401


async def test_statements_for_unknown_product_returns_404(authenticated_client):
    resp = await authenticated_client.get(f"/api/v1/internal/products/{uuid.uuid4()}/statements")
    assert resp.status_code == 404


async def test_statement_period_with_no_activity_returns_404(authenticated_client):
    product_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 5_000_000.0,
            "ea_rate": 0.36,
            "day_count_basis": 365,
        },
    )
    product = product_resp.json()

    resp = await authenticated_client.get(
        f"/api/v1/internal/products/{product['id']}/statements/2026-01-01"
    )
    assert resp.status_code == 404
