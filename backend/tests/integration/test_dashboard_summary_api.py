from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from app.accounts.security import create_session_token
from app.core.config import settings
from app.main import app
from tests.integration.conftest import create_test_user

pytestmark = pytest.mark.anyio


async def test_empty_dashboard_is_all_zeros(authenticated_client):
    resp = await authenticated_client.get("/api/v1/internal/products/dashboard-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["co"] == {"total_balance": 0.0, "total_interest": 0.0, "total_fees": 0.0}
    assert data["us"] == {"total_balance": 0.0, "total_interest": 0.0, "total_fees": 0.0}
    assert data["highest_cost_product_id"] is None


async def test_co_only_dashboard_does_not_touch_us_bucket(authenticated_client):
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

    await authenticated_client.post(
        f"/api/v1/internal/products/{product['id']}/purchases",
        json={
            "amount": 300_000.0,
            "currency": "COP",
            "purchase_date": str(date.today()),
            "n_installments": 3,
            "interest_free_promo": True,
        },
    )

    resp = await authenticated_client.get("/api/v1/internal/products/dashboard-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["co"]["total_balance"] == pytest.approx(300_000.0)
    assert data["us"] == {"total_balance": 0.0, "total_interest": 0.0, "total_fees": 0.0}
    assert data["highest_cost_product_id"] == product["id"]


async def test_mixed_co_and_us_cards_stay_in_separate_buckets(authenticated_client):
    co_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 5_000_000.0,
            "ea_rate": 0.20,
            "day_count_basis": 365,
        },
    )
    co_product = co_resp.json()
    await authenticated_client.post(
        f"/api/v1/internal/products/{co_product['id']}/purchases",
        json={
            "amount": 300_000.0,
            "currency": "COP",
            "purchase_date": str(date.today()),
            "n_installments": 1,
            "interest_free_promo": True,
        },
    )

    us_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "US",
            "institution_name": "Chase",
            "credit_limit": 10_000.0,
            "day_count_basis": 365,
            "apr": 0.30,
        },
    )
    us_product = us_resp.json()
    await authenticated_client.post(
        f"/api/v1/internal/products/{us_product['id']}/purchases",
        json={
            "amount": 500.0,
            "currency": "USD",
            "purchase_date": str(date.today()),
        },
    )

    resp = await authenticated_client.get("/api/v1/internal/products/dashboard-summary")
    assert resp.status_code == 200
    data = resp.json()

    # CO's balance is in COP-scale, US's in USD-scale -- never summed together
    assert data["co"]["total_balance"] == pytest.approx(300_000.0)
    assert data["us"]["total_balance"] == pytest.approx(500.0)

    # US has the higher disclosed rate (0.30 APR vs 0.20 EA), so it's flagged
    assert data["highest_cost_product_id"] == us_product["id"]


async def test_highest_cost_flags_the_highest_disclosed_rate_among_co_cards(authenticated_client):
    low_rate_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco Bajo",
            "credit_limit": 1_000_000.0,
            "ea_rate": 0.20,
            "day_count_basis": 365,
        },
    )
    high_rate_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco Alto",
            "credit_limit": 1_000_000.0,
            "ea_rate": 0.55,
            "day_count_basis": 365,
        },
    )
    high_rate_product = high_rate_resp.json()
    assert low_rate_resp.status_code == 201

    resp = await authenticated_client.get("/api/v1/internal/products/dashboard-summary")
    data = resp.json()
    assert data["highest_cost_product_id"] == high_rate_product["id"]


async def test_dashboard_summary_requires_authentication(async_client):
    resp = await async_client.get("/api/v1/internal/products/dashboard-summary")
    assert resp.status_code == 401


async def test_dashboard_summary_only_includes_current_users_cards(authenticated_client):
    await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 5_000_000.0,
            "ea_rate": 0.36,
            "day_count_basis": 365,
        },
    )

    other_user = await create_test_user(
        authenticated_client.session_factory, email="other-dashboard@example.com"
    )
    other_token = create_session_token(other_user.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as other_client:
        other_client.cookies.set(settings.session_cookie_name, other_token)
        resp = await other_client.get("/api/v1/internal/products/dashboard-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["co"]["total_balance"] == 0.0
