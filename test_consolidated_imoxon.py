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

@pytest.mark.anyio
async def test_supplier_product_import(client, admin_headers):
    # Connect
    res = await client.post("/imoxon/suppliers/connect", params={"name": "Test Global"}, headers=admin_headers)
    sid = res.json()["supplier_id"]
    # Import
    res = await client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Item 1", "price": 100}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Item 1"

@pytest.mark.anyio
async def test_product_approval_required(client, admin_headers):
    # Import
    res = await client.post("/imoxon/suppliers/connect", params={"name": "Supplier X"}, headers=admin_headers)
    sid = res.json()["supplier_id"]
    res = await client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Secret Item", "price": 10}, headers=admin_headers)
    pid = res.json()["id"]
    # Check Catalog (should be empty for unapproved)
    res = await client.get("/imoxon/catalog", headers=admin_headers)
    assert pid not in res.json()
    # Approve
    await client.post("/imoxon/products/approve", params={"pid": pid}, headers=admin_headers)
    res = await client.get("/imoxon/catalog", headers=admin_headers)
    assert pid in res.json()

@pytest.mark.anyio
async def test_landed_cost_calculation(client, admin_headers):
    # Base: 100
    # Ship/Cust (15%): 15 -> 115
    # Markup (10% on 115): 11.5 -> 126.5
    # FCE SC (10% on 126.5): 12.65 -> 139.15
    # FCE TGST (17% on 139.15): 23.66 -> 162.81
    res = await client.post("/imoxon/pricing/landed-cost", params={"base": 100, "cat": "RESORT_SUPPLY"}, headers=admin_headers)
    assert res.json()["total"] == 162.81

@pytest.mark.anyio
async def test_no_direct_db_write():
    from main import shadow_core
    with pytest.raises(PermissionError):
        shadow_core.commit("manual.hack", "SYSTEM", {"data": "rogue"})
