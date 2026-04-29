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

    # Bind device - Fix: identity_id is query param
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
async def test_supplier_product_import(client, headers):
    # Test catalog import via ImoxonCore
    res = await client.post("/imoxon/suppliers/connect?name=TestSupplier", headers=headers)
    sid = res.json()["supplier_id"]

    payload = {"name": "Maldivian Tuna", "price": 100}
    res = await client.post(f"/imoxon/products/import?sid={sid}", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "PENDING_APPROVAL"
    assert "id" in res.json()

@pytest.mark.anyio
async def test_product_approval_required(client, headers):
    res = await client.post("/imoxon/suppliers/connect?name=TestSupplier", headers=headers)
    sid = res.json()["supplier_id"]

    import_res = await client.post(f"/imoxon/products/import?sid={sid}", json={"name": "Gold", "price": 500}, headers=headers)
    pid = import_res.json()["id"]

    # Approve
    approve_res = await client.post(f"/imoxon/products/approve?pid={pid}", headers=headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"

@pytest.mark.anyio
async def test_landed_cost_calculation(client, headers):
    # Base 100 -> Landed = 100 * 1.15 (Logistics) * 1.10 (Markup) = 126.5
    res = await client.post("/imoxon/suppliers/connect?name=TestSupplier", headers=headers)
    sid = res.json()["supplier_id"]

    import_res = await client.post(f"/imoxon/products/import?sid={sid}", json={"name": "Sea Salt", "price": 100}, headers=headers)
    assert import_res.json()["landed_base"] == 126.5

@pytest.mark.anyio
async def test_no_direct_db_write():
    from main import shadow_core
    with pytest.raises(PermissionError):
        shadow_core.commit("manual.hack", "ROGUE", {"data": "rogue"})
