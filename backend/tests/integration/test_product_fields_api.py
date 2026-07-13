import pytest

pytestmark = pytest.mark.anyio


async def test_new_fields_default_sensibly_when_omitted(authenticated_client):
    resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 5_000_000.0,
            "ea_rate": 0.36,
            "day_count_basis": 365,
        },
    )
    assert resp.status_code == 201
    product = resp.json()
    assert product["recurring_fee"] is None
    assert product["insurance_opt_in"] is False
    assert product["insurance_cost"] is None
    assert product["fx_fee"] is None
    assert product["co_single_installment_charges_interest"] is False


async def test_create_with_recurring_fee_and_fx_fee(authenticated_client):
    resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 5_000_000.0,
            "ea_rate": 0.36,
            "day_count_basis": 365,
            "recurring_fee": 15_000.0,
            "fx_fee": 0.03,
            "co_single_installment_charges_interest": True,
        },
    )
    assert resp.status_code == 201
    product = resp.json()
    assert product["recurring_fee"] == 15_000.0
    assert product["fx_fee"] == 0.03
    assert product["co_single_installment_charges_interest"] is True


async def test_insurance_opt_in_requires_insurance_cost(authenticated_client):
    resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 5_000_000.0,
            "ea_rate": 0.36,
            "day_count_basis": 365,
            "insurance_opt_in": True,
        },
    )
    assert resp.status_code == 422


async def test_insurance_opt_in_with_cost_succeeds(authenticated_client):
    resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "US",
            "institution_name": "Chase",
            "credit_limit": 10_000.0,
            "day_count_basis": 365,
            "apr": 0.24,
            "insurance_opt_in": True,
            "insurance_cost": 4.99,
        },
    )
    assert resp.status_code == 201
    product = resp.json()
    assert product["insurance_opt_in"] is True
    assert product["insurance_cost"] == 4.99


async def test_negative_recurring_fee_rejected(authenticated_client):
    resp = await authenticated_client.post(
        "/api/v1/internal/products",
        json={
            "market": "CO",
            "institution_name": "Banco de Prueba",
            "credit_limit": 5_000_000.0,
            "ea_rate": 0.36,
            "day_count_basis": 365,
            "recurring_fee": -1000.0,
        },
    )
    assert resp.status_code == 422


async def test_update_new_fields(authenticated_client):
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

    update_resp = await authenticated_client.patch(
        f"/api/v1/internal/products/{product['id']}",
        json={
            "recurring_fee": 12_000.0,
            "insurance_opt_in": True,
            "insurance_cost": 5_000.0,
            "fx_fee": 0.025,
            "co_single_installment_charges_interest": True,
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["recurring_fee"] == 12_000.0
    assert updated["insurance_opt_in"] is True
    assert updated["insurance_cost"] == 5_000.0
    assert updated["fx_fee"] == 0.025
    assert updated["co_single_installment_charges_interest"] is True
