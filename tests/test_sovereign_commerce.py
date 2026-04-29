import pytest
from httpx import ASGITransport, AsyncClient
from main import app
import uuid

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def headers(client):
    # Setup authorized actor
    res = await client.post("/imoxon/aegis/identity/create", json={"full_name": "Test Admin", "profile_type": "admin"})
    identity_id = res.json()["identity_id"]

    # Bind device
    res = await client.post(f"/imoxon/aegis/identity/device/bind?identity_id={identity_id}", json={"device_name": "Test Device"})
    if res.status_code != 200:
        raise RuntimeError(f"Device bind failed: {res.text}")
    device_id = res.json()["device_id"]

    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

@pytest.mark.anyio
async def test_unsigned_request_rejected(client):
    res = await client.post("/imoxon/orders/create", json={})
    assert res.status_code in [401, 403]
    detail = res.json()["detail"]
    assert "Missing Identity" in detail or "Unauthorized direct write" in detail or "EXECUTION GUARD REJECTION" in detail

@pytest.mark.anyio
async def test_missing_device_rejected(client):
    headers = {"X-AEGIS-IDENTITY": "actor-123"}
    res = await client.post("/imoxon/orders/create", json={}, headers=headers)
    assert res.status_code in [401, 403]
    detail = res.json()["detail"]
    assert "Missing Identity" in detail or "Unauthorized direct write" in detail or "EXECUTION GUARD REJECTION" in detail

@pytest.mark.anyio
async def test_maldives_billing_math(client, headers):
    # Base 100 -> Created PR
    payload = {"items": ["Luxury Villa"], "amount": 100, "product_type": "PACKAGE", "tax_type": "TOURISM_STANDARD"}
    res = await client.post("/imoxon/orders/create", json=payload, headers=headers)
    assert res.status_code == 200
    order_id = res.json()["id"]

    # Approve
    await client.post(f"/imoxon/orders/approve?order_id={order_id}", headers=headers)

    # Invoice - This is where FCE calculation happens for procurement
    res = await client.post(f"/imoxon/orders/invoice?order_id={order_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    # FCE billing rule (RC1): Base + 10% SC = 110. 17% TGST on 110 = 18.7. Total = 128.7
    assert data["pricing"]["service_charge"] == 10.0
    assert data["pricing"]["tax_amount"] == 18.7
    assert data["pricing"]["total_input_currency"] == 128.7

@pytest.mark.anyio
async def test_shadow_audit_creation(client, headers):
    payload = {"items": ["Item A"], "amount": 50, "product_type": "RETAIL", "tax_type": "RETAIL"}
    await client.post("/imoxon/orders/create", json=payload, headers=headers)

    # Verify health check shows integrity
    res = await client.get("/health")
    assert res.json()["integrity"] is True

@pytest.mark.anyio
async def test_failed_transaction_rollback(client, headers):
    # Try to approve non-existent order - Updated for correct exception message matching
    res = await client.post("/imoxon/orders/approve?order_id=NONEXISTENT", headers=headers)
    assert res.status_code == 500
    assert "SOVEREIGN EXECUTION FAILED" in res.json()["detail"]
    assert "Order not found" in res.json()["detail"]
