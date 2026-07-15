import pytest
import httpx
from main import app
from httpx import ASGITransport
from decimal import Decimal

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
async def headers(client):
    # Setup authorized actor
    res = await client.post("/imoxon/aegis/identity/create", json={"full_name": "Test Admin", "profile_type": "admin"})
    actor_id = res.json()["identity_id"]
    res_dev = await client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "test-dev"})
    device_id = res_dev.json()["device_id"]
    # Verify identity for critical actions
    await client.post("/imoxon/aegis/identity/verify", params={"identity_id": actor_id, "verifier_id": "SYSTEM"})

    return {
        "X-AEGIS-IDENTITY": actor_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"
    }

@pytest.mark.anyio
async def test_unsigned_request_rejected(client):
    res = await client.post("/imoxon/orders/create", json={})
    # Doctrine: 401 for missing credentials
    assert res.status_code == 401
    assert "Missing Identity, Device or Signature" in res.json()["detail"]

@pytest.mark.anyio
async def test_missing_device_rejected(client):
    headers = {"X-AEGIS-IDENTITY": "actor-123"}
    res = await client.post("/imoxon/orders/create", json={}, headers=headers)
    assert res.status_code == 401

@pytest.mark.anyio
async def test_maldives_billing_math(client, headers):
    # Standard FCE test
    from main import fce_core
    fce_res = fce_core.finalize_invoice(Decimal("1000"), "TOURISM")
    assert fce_res["total"] == 1287.0
    assert fce_res["tax_rate"] == 0.17

@pytest.mark.anyio
async def test_shadow_audit_creation(client, headers):
    from main import shadow_core
    initial_len = len(shadow_core.chain)
    # connect_supplier in main.py creates one commerce action (Intent + Committed)
    await client.post("/imoxon/suppliers/connect", params={"name": "Audit Test"}, headers=headers)
    assert len(shadow_core.chain) >= initial_len + 2
    last_block = shadow_core.chain[-1]
    assert last_block["event_type"].startswith("imoxon.supplier.connect")
    assert last_block["actor_id"] == headers["X-AEGIS-IDENTITY"]

@pytest.mark.anyio
async def test_unauthorized_mutation_rejection(client):
    # Try to approve product without valid admin headers
    res = await client.post("/imoxon/products/approve", params={"pid": "123"})
    assert res.status_code == 401
