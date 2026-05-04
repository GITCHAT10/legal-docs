import pytest
import httpx
import os
from main import app
from httpx import ASGITransport

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
    res = await client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "test-dev"})
    device_id = res.json()["device_id"]
    await client.post("/imoxon/aegis/identity/verify", params={"identity_id": actor_id, "verifier_id": "SYSTEM"})
    return {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": device_id, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"}

@pytest.mark.anyio
async def test_supplier_product_import(client, headers):
    res = await client.post("/imoxon/suppliers/connect", params={"name": "Test Global"}, headers=headers)
    if res.status_code != 200:
        print(f"DEBUG: connect_supplier failed with {res.status_code}: {res.text}")
    assert res.status_code == 200
    sid = res.json().get("supplier_id")
    res = await client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Item 1", "price": 100}, headers=headers)
    assert res.status_code == 200
    assert "id" in res.json()

@pytest.mark.anyio
async def test_product_approval_required(client, headers):
    res = await client.post("/imoxon/suppliers/connect", params={"name": "Supplier X"}, headers=headers)
    sid = res.json().get("supplier_id")
    res = await client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Secret Item", "price": 10}, headers=headers)
    pid = res.json()["id"]
    assert res.json()["status"] == "PENDING_APPROVAL"
    res = await client.post("/imoxon/products/approve", params={"pid": pid}, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"

@pytest.mark.anyio
async def test_landed_cost_calculation(client, headers):
    res = await client.post("/imoxon/pricing/landed-cost", params={"base": 100, "cat": "RESORT_SUPPLY"}, headers=headers)
    assert res.json()["total"] == 162.81

@pytest.mark.anyio
async def test_no_direct_db_write():
    from main import shadow_core
    from mnos.shared.execution_guard import _sovereign_context
    _sovereign_context.set(None)
    with pytest.raises(PermissionError):
        shadow_core.commit("manual.hack", "HACKER", {"data": "rogue"})
