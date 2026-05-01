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
    data = res.json()
    actor_id = data.get("identity_id") or data.get("id")
    if not actor_id:
        raise ValueError(f"Failed to create identity: {data}")

    res = await client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "test-dev"})
    data = res.json()
    device_id = data.get("device_id")
    if not device_id:
        raise ValueError(f"Failed to bind device: {data}")

    return {
        "X-AEGIS-IDENTITY": str(actor_id),
        "X-AEGIS-DEVICE": str(device_id),
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"
    }

@pytest.mark.anyio
async def test_supplier_product_import(client, headers):
    # Connect
    res = await client.post("/imoxon/suppliers/connect", json={"name": "Test Global", "type": "GLOBAL"}, headers=headers)
    sid = res.json()["id"]
    # Import
    res = await client.post("/imoxon/products/import", params={"sid": sid}, json=[{"name": "Item 1", "price": 100}], headers=headers)
    assert res.status_code == 200
    assert len(res.json()["products"]) == 1

@pytest.mark.anyio
async def test_product_approval_required(client, headers):
    # Import
    res = await client.post("/imoxon/suppliers/connect", json={"name": "Supplier X"}, headers=headers)
    sid = res.json()["id"]
    res = await client.post("/imoxon/products/import", params={"sid": sid}, json=[{"name": "Secret Item", "price": 10}], headers=headers)
    pid = res.json()["products"][0]["id"]
    # Check Catalog (should be empty)
    res = await client.get("/imoxon/catalog", headers=headers)
    assert pid not in res.json()
    # Approve
    await client.post("/imoxon/products/approve", params={"pid": pid}, headers=headers)
    res = await client.get("/imoxon/catalog", headers=headers)
    assert pid in res.json()

@pytest.mark.anyio
async def test_landed_cost_calculation(client, headers):
    # Base: 100
    # FCE SC (10% on 100): 10 -> 110
    # FCE TGST (17% on 110): 18.7 -> 128.7
    res = await client.post("/imoxon/pricing/landed-cost", params={"base": 100, "cat": "RESORT_SUPPLY"}, headers=headers)
    assert res.json()["total"] == 128.7

@pytest.mark.anyio
async def test_no_direct_db_write():
    from main import shadow_core
    with pytest.raises(PermissionError):
        shadow_core.commit("manual.hack", "SYSTEM", {"data": "rogue"}, trace_id="TEST-TRACE")
