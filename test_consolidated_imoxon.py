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
    # Setup authorized actor - Admin for connection and import
    res = await client.post("/imoxon/aegis/identity/create", json={"full_name": "Test Procurement", "profile_type": "admin"})
    actor_id = res.json()["identity_id"]
    await client.post("/imoxon/aegis/identity/verify", params={"identity_id": actor_id, "verifier_id": "SYSTEM"})
    res = await client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "test-dev"})
    device_id = res.json()["device_id"]
    return {
        "X-AEGIS-IDENTITY": actor_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"
    }

@pytest.mark.anyio
async def test_supplier_product_import(client, headers):
    # Connect
    res = await client.post("/imoxon/suppliers/connect", params={"name": "Test Global"}, headers=headers)
    assert res.status_code == 200
    sid = res.json()["supplier_id"]

    # Import
    res = await client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Item 1", "price": 100}, headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Item 1"

@pytest.mark.anyio
async def test_product_approval_required(client, headers):
    # Import
    res = await client.post("/imoxon/suppliers/connect", params={"name": "Supplier X"}, headers=headers)
    sid = res.json()["supplier_id"]
    res = await client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Secret Item", "price": 10}, headers=headers)
    pid = res.json()["id"]

    # Approve
    res = await client.post("/imoxon/products/approve", params={"pid": pid}, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"

@pytest.mark.anyio
async def test_no_direct_db_write():
    from main import shadow_core
    from mnos.shared.execution_guard import ExecutionGuard

    # Direct write should fail
    with pytest.raises(PermissionError, match="FAIL CLOSED"):
        shadow_core.commit("manual.hack", "actor", {"data": "rogue"})

    # Authorized context should allow it
    with ExecutionGuard.authorized_context({"identity_id": "SYS", "role": "admin"}):
        h = shadow_core.commit("manual.hack", "actor", {"data": "safe"})
        assert h is not None
