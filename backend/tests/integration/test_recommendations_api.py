import uuid
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from app.accounts.security import create_session_token
from app.core.config import settings
from app.main import app
from tests.integration.conftest import create_test_user

pytestmark = pytest.mark.anyio


async def test_empty_recommendations_when_no_cards(authenticated_client):
    resp = await authenticated_client.get("/api/v1/internal/products/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {
        "real_cost_exceeds_rate": [],
        "pay_in_full_saves_interest": [],
        "promo_expiring": [],
        "avalanche_payoff_order": [],
        "utilization_risk": [],
    }


async def test_promo_expiring_flag_for_co_card(authenticated_client):
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

    purchase_resp = await authenticated_client.post(
        f"/api/v1/internal/products/{product['id']}/purchases",
        json={
            "amount": 300_000.0,
            "currency": "COP",
            "purchase_date": "2026-01-15",
            "n_installments": 3,
            "interest_free_promo": True,
            "description": "TV a cuotas",
        },
    )
    purchase = purchase_resp.json()

    resp = await authenticated_client.get(f"/api/v1/internal/products/{product['id']}/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    # As of "today" (system date 2026-07-13 per environment), this 3-month
    # promo starting Jan 15 2026 has long since completed, so it should
    # NOT still be flagged as expiring -- confirms completed promos are
    # excluded, not just a smoke test.
    assert data["promo_expiring"] == []
    assert purchase["interest_free_promo"] is True


async def test_promo_expiring_flag_fires_near_purchase_time(authenticated_client):
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

    today = date.today()
    purchase_resp = await authenticated_client.post(
        f"/api/v1/internal/products/{product['id']}/purchases",
        json={
            "amount": 300_000.0,
            "currency": "COP",
            "purchase_date": str(today),
            "n_installments": 1,
            "interest_free_promo": True,
        },
    )
    purchase = purchase_resp.json()

    resp = await authenticated_client.get(f"/api/v1/internal/products/{product['id']}/recommendations")
    data = resp.json()
    assert len(data["promo_expiring"]) == 1
    assert data["promo_expiring"][0]["purchase_id"] == purchase["id"]
    assert data["promo_expiring"][0]["installments_remaining"] == 1


async def test_us_card_pay_in_full_saves_interest_flag(authenticated_client):
    product_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "US",
            "institution_name": "Chase",
            "credit_limit": 10_000.0,
            "day_count_basis": 365,
            "apr": 0.24,
        },
    )
    product = product_resp.json()

    today = date.today()
    await authenticated_client.post(
        f"/api/v1/internal/products/{product['id']}/purchases",
        json={"amount": 1_000.0, "currency": "USD", "purchase_date": str(today)},
    )

    resp = await authenticated_client.get(f"/api/v1/internal/products/{product['id']}/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["pay_in_full_saves_interest"]) == 1
    flag = data["pay_in_full_saves_interest"][0]
    assert flag["product_id"] == product["id"]
    assert flag["current_period_interest"] > 0
    assert flag["statement_balance"] == pytest.approx(1_000.0)


async def test_utilization_risk_flag(authenticated_client):
    product_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 1_000_000.0,
            "ea_rate": 0.36,
            "day_count_basis": 365,
        },
    )
    product = product_resp.json()

    await authenticated_client.post(
        f"/api/v1/internal/products/{product['id']}/purchases",
        json={
            "amount": 800_000.0,
            "currency": "COP",
            "purchase_date": str(date.today()),
            "n_installments": 1,
            "interest_free_promo": True,
        },
    )

    resp = await authenticated_client.get("/api/v1/internal/products/recommendations")
    data = resp.json()
    assert len(data["utilization_risk"]) == 1
    flag = data["utilization_risk"][0]
    assert flag["product_id"] == product["id"]
    assert flag["utilization"] == pytest.approx(0.8)


async def test_avalanche_order_ranks_across_markets_and_dashboard_wide(authenticated_client):
    co_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco Bajo",
            "credit_limit": 2_000_000.0,
            "ea_rate": 0.18,
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
            "institution_name": "Amex",
            "credit_limit": 8_000.0,
            "day_count_basis": 365,
            "apr": 0.28,
        },
    )
    us_product = us_resp.json()
    await authenticated_client.post(
        f"/api/v1/internal/products/{us_product['id']}/purchases",
        json={"amount": 500.0, "currency": "USD", "purchase_date": str(date.today())},
    )

    dashboard_resp = await authenticated_client.get("/api/v1/internal/products/recommendations")
    order = [e["product_id"] for e in dashboard_resp.json()["avalanche_payoff_order"]]
    assert order == [us_product["id"], co_product["id"]]

    # Per-card view for the CO card still shows the full cross-card order for context
    per_card_resp = await authenticated_client.get(
        f"/api/v1/internal/products/{co_product['id']}/recommendations"
    )
    per_card_order = [e["product_id"] for e in per_card_resp.json()["avalanche_payoff_order"]]
    assert per_card_order == order

    # But card-specific flags are filtered to just that card
    per_card_data = per_card_resp.json()
    assert all(
        f["product_id"] == co_product["id"] for f in per_card_data["utilization_risk"]
    )


async def test_recommendations_require_authentication(async_client):
    resp = await async_client.get("/api/v1/internal/products/recommendations")
    assert resp.status_code == 401


async def test_product_recommendations_for_unknown_product_returns_404(authenticated_client):
    resp = await authenticated_client.get(
        f"/api/v1/internal/products/{uuid.uuid4()}/recommendations"
    )
    assert resp.status_code == 404


async def test_recommendations_only_include_current_users_cards(authenticated_client):
    await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 1_000_000.0,
            "ea_rate": 0.36,
            "day_count_basis": 365,
        },
    )

    other_user = await create_test_user(
        authenticated_client.session_factory, email="other-recs@example.com"
    )
    other_token = create_session_token(other_user.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as other_client:
        other_client.cookies.set(settings.session_cookie_name, other_token)
        resp = await other_client.get("/api/v1/internal/products/recommendations")
        assert resp.status_code == 200
        assert resp.json()["avalanche_payoff_order"] == []
