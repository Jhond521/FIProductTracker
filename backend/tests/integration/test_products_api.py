import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.accounts.security import create_session_token
from app.core.config import settings
from app.main import app
from tests.integration.conftest import create_test_user

pytestmark = pytest.mark.anyio


async def test_full_flow_create_product_purchase_and_get_schedule(authenticated_client):
    # 1. Create a Colombian credit card product
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
    assert product_resp.status_code == 201
    product = product_resp.json()
    assert product["market"] == "CO"

    # 2. Add a purchase deferred into 6 installments
    purchase_resp = await authenticated_client.post(
        f"/api/v1/internal/products/{product['id']}/purchases",
        json={
            "amount": 600_000.0,
            "currency": "COP",
            "purchase_date": "2026-07-01",
            "n_installments": 6,
            "interest_free_promo": False,
            "description": "Electrodomestico",
        },
    )
    assert purchase_resp.status_code == 201
    purchase = purchase_resp.json()

    # 3. Get the amortization schedule — the actual product value
    schedule_resp = await authenticated_client.get(
        f"/api/v1/internal/products/{product['id']}/purchases/{purchase['id']}/schedule"
    )
    assert schedule_resp.status_code == 200
    data = schedule_resp.json()

    assert len(data["schedule"]) == 6
    assert data["total_interest_cost"] > 0
    assert data["schedule"][-1]["remaining_balance"] == 0.0

    # Principal portions should sum back to the original purchase amount
    total_principal = sum(e["principal_portion"] for e in data["schedule"])
    assert total_principal == pytest.approx(600_000.0, rel=1e-3)


async def test_interest_free_promo_purchase_has_zero_interest(authenticated_client):
    product_resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 5_000_000.0,
            "ea_rate": 0.45,
            "day_count_basis": 365,
        },
    )
    product = product_resp.json()

    purchase_resp = await authenticated_client.post(
        f"/api/v1/internal/products/{product['id']}/purchases",
        json={
            "amount": 300_000.0,
            "currency": "COP",
            "purchase_date": "2026-07-01",
            "n_installments": 3,
            "interest_free_promo": True,
        },
    )
    purchase = purchase_resp.json()

    schedule_resp = await authenticated_client.get(
        f"/api/v1/internal/products/{product['id']}/purchases/{purchase['id']}/schedule"
    )
    data = schedule_resp.json()

    assert data["total_interest_cost"] == 0.0
    assert all(e["interest_portion"] == 0.0 for e in data["schedule"])


async def test_purchase_not_found_returns_404(authenticated_client):
    resp = await authenticated_client.get(
        f"/api/v1/internal/products/{uuid.uuid4()}/purchases/{uuid.uuid4()}/schedule"
    )
    assert resp.status_code == 404


async def test_list_products_returns_all_created_products(authenticated_client):
    for name in ("Banco Uno", "Banco Dos"):
        resp = await authenticated_client.post(
            "/api/v1/internal/products",
            json={
                "market": "CO",
                "institution_name": name,
                "credit_limit": 1_000_000.0,
                "ea_rate": 0.30,
                "day_count_basis": 365,
            },
        )
        assert resp.status_code == 201

    list_resp = await authenticated_client.get("/api/v1/internal/products")
    assert list_resp.status_code == 200
    names = {p["institution_name"] for p in list_resp.json()}
    assert {"Banco Uno", "Banco Dos"}.issubset(names)


async def test_list_purchases_for_product(authenticated_client):
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
            "amount": 100_000.0,
            "currency": "COP",
            "purchase_date": "2026-07-01",
            "n_installments": 3,
        },
    )

    list_resp = await authenticated_client.get(f"/api/v1/internal/products/{product['id']}/purchases")
    assert list_resp.status_code == 200
    purchases = list_resp.json()
    assert len(purchases) == 1
    assert purchases[0]["amount"] == 100_000.0


async def test_list_purchases_for_unknown_product_returns_404(authenticated_client):
    resp = await authenticated_client.get(f"/api/v1/internal/products/{uuid.uuid4()}/purchases")
    assert resp.status_code == 404


async def test_products_require_authentication(async_client):
    resp = await async_client.get("/api/v1/internal/products")
    assert resp.status_code == 401


async def test_user_cannot_access_another_users_product(authenticated_client):
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

    other_user = await create_test_user(
        authenticated_client.session_factory, email="other@example.com"
    )
    other_token = create_session_token(other_user.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as other_client:
        other_client.cookies.set(settings.session_cookie_name, other_token)

        resp = await other_client.get(f"/api/v1/internal/products/{product['id']}")
        assert resp.status_code == 404

        list_resp = await other_client.get("/api/v1/internal/products")
        assert list_resp.status_code == 200
        assert list_resp.json() == []
