import pytest
import httpx
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
    res_dev = await client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "test-dev"})
    device_id = res_dev.json()["device_id"]
    # Verify identity
    await client.post("/imoxon/aegis/identity/verify", params={"identity_id": actor_id, "verifier_id": "SYSTEM"})

    return {
        "X-AEGIS-IDENTITY": actor_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"
    }

@pytest.mark.anyio
async def test_supplier_product_import(client, headers):
    # Connect
    res = await client.post("/imoxon/suppliers/connect", params={"name": "Test Global"}, headers=headers)
    sid = res.json()["supplier_id"]
    # Import
    res = await client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Item 1", "price": 100}, headers=headers)
    assert res.status_code == 200
    assert "Item 1" in res.json()["name"]

@pytest.mark.anyio
async def test_product_approval_required(client, headers):
    # Import
    res = await client.post("/imoxon/suppliers/connect", params={"name": "Supplier X"}, headers=headers)
    sid = res.json()["supplier_id"]
    res = await client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Secret Item", "price": 10}, headers=headers)
    pid = res.json()["id"]
    # Check Catalog (using specialized catalog check if available, or just check result)
    assert res.json()["status"] == "PENDING_APPROVAL"
    # Approve
    res_app = await client.post("/imoxon/products/approve", params={"pid": pid}, headers=headers)
    assert res_app.json()["status"] == "APPROVED"

@pytest.mark.anyio
async def test_no_direct_db_write():
    from main import shadow_core
    with pytest.raises(PermissionError):
        # shadow_core.commit(event_type, actor_id, payload)
        shadow_core.commit("manual.hack", "malicious-actor", {"data": "rogue"})
