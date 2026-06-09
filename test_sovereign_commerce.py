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
async def test_unsigned_request_rejected(client):
    res = await client.post("/imoxon/orders/create", json={})
    assert res.status_code == 401
    assert "AEGIS_REQUIRED" in res.json()["detail"]

@pytest.mark.anyio
async def test_missing_device_rejected(client):
    headers = {"X-AEGIS-IDENTITY": "actor-123"}
    res = await client.post("/imoxon/orders/create", json={}, headers=headers)
    assert res.status_code == 401
    assert "AEGIS_REQUIRED" in res.json()["detail"]

@pytest.mark.anyio
async def test_maldives_billing_math(client, admin_headers):
    # Base: 1000
    # Ship/Cust (15%): 150 -> 1150
    # Markup (10%): 115 -> 1265
    # Landed Base: 1265
    # SC (10% on 1265): 126.5 -> 1391.5
    # TGST (17% on 1391.5): 236.56 -> 1628.06
    res = await client.post("/imoxon/pricing/landed-cost", params={"base": 1000, "cat": "RESORT_SUPPLY"}, headers=admin_headers)
    pricing = res.json()
    assert pricing["total"] == 1628.06
    # Standard FCE test without landed engine overhead
    from main import fce_core
    fce_res = fce_core.finalize_invoice(1000, "TOURISM")
    assert fce_res["total"] == 1287.0
    assert fce_res["tax_rate"] == 0.17

@pytest.mark.anyio
async def test_shadow_audit_creation(client, admin_headers):
    from main import shadow_core
    initial_len = len(shadow_core.chain)
    await client.post("/imoxon/suppliers/connect", params={"name": "Audit Test"}, headers=admin_headers)
    # Each execute_sovereign_action creates 2 entries (Intent + Committed)
    # BUT connect_supplier also calls identity_core.create_profile which is 1 commit
    # HOWEVER, in the current session, many things might be happening.
    # Let's check relative growth.
    assert len(shadow_core.chain) >= initial_len + 3
    last_block = shadow_core.get_block(len(shadow_core.chain)-1)
    assert last_block["payload"]["status"] == "COMMITTED"
    assert last_block["actor_id"] == admin_headers["X-AEGIS-IDENTITY"]

@pytest.mark.anyio
async def test_failed_transaction_rollback(client, admin_headers):
    # Attempt to approve non-existent product
    res = await client.post("/imoxon/products/approve", params={"pid": "none"}, headers=admin_headers)
    # RuntimeError unhandled is 500, but we added a handler in main.py mapping it to 404 for "not in queue"
    assert res.status_code == 404

    from main import shadow_core
    last_block = shadow_core.get_block(len(shadow_core.chain)-1)
    assert last_block["payload"]["status"] == "FAILED_ROLLBACK"

@pytest.mark.anyio
async def test_unauthorized_mutation_rejection(client):
    # Try to approve product without valid admin headers
    res = await client.post("/imoxon/products/approve", params={"pid": "123"})
    assert res.status_code == 401
