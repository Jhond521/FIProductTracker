import pytest

pytestmark = pytest.mark.anyio


async def test_full_flow_create_product_purchase_and_get_schedule(async_client):
    # 1. Create a Colombian credit card product
    product_resp = await async_client.post(
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
    purchase_resp = await async_client.post(
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
    schedule_resp = await async_client.get(
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


async def test_interest_free_promo_purchase_has_zero_interest(async_client):
    product_resp = await async_client.post(
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

    purchase_resp = await async_client.post(
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

    schedule_resp = await async_client.get(
        f"/api/v1/internal/products/{product['id']}/purchases/{purchase['id']}/schedule"
    )
    data = schedule_resp.json()

    assert data["total_interest_cost"] == 0.0
    assert all(e["interest_portion"] == 0.0 for e in data["schedule"])


async def test_purchase_not_found_returns_404(async_client):
    import uuid

    resp = await async_client.get(
        f"/api/v1/internal/products/{uuid.uuid4()}/purchases/{uuid.uuid4()}/schedule"
    )
    assert resp.status_code == 404


async def test_list_products_returns_all_created_products(async_client):
    for name in ("Banco Uno", "Banco Dos"):
        resp = await async_client.post(
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

    list_resp = await async_client.get("/api/v1/internal/products")
    assert list_resp.status_code == 200
    names = {p["institution_name"] for p in list_resp.json()}
    assert {"Banco Uno", "Banco Dos"}.issubset(names)


async def test_list_purchases_for_product(async_client):
    product_resp = await async_client.post(
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

    await async_client.post(
        f"/api/v1/internal/products/{product['id']}/purchases",
        json={
            "amount": 100_000.0,
            "currency": "COP",
            "purchase_date": "2026-07-01",
            "n_installments": 3,
        },
    )

    list_resp = await async_client.get(f"/api/v1/internal/products/{product['id']}/purchases")
    assert list_resp.status_code == 200
    purchases = list_resp.json()
    assert len(purchases) == 1
    assert purchases[0]["amount"] == 100_000.0


async def test_list_purchases_for_unknown_product_returns_404(async_client):
    import uuid

    resp = await async_client.get(f"/api/v1/internal/products/{uuid.uuid4()}/purchases")
    assert resp.status_code == 404
