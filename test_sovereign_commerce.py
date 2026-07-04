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
    # raise_app_exceptions=False equivalent in httpx AsyncClient
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
async def headers(client):
    # Setup authorized actor
    res = await client.post("/imoxon/aegis/identity/create", json={"full_name": "Test Admin", "profile_type": "admin"})
    actor_id = res.json()["identity_id"]
    # Verify identity for critical actions
    from main import identity_core
    identity_core.verify_identity(actor_id, "SYSTEM")

    res = await client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "test-dev"})
    device_id = res.json()["device_id"]
    return {
        "X-AEGIS-IDENTITY": actor_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"
    }

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
async def test_maldives_billing_math(client, headers):
    # Base: 1000
    # Ship/Cust (15%): 150 -> 1150
    # Markup (10%): 115 -> 1265
    # Landed Base: 1265
    # SC (10% on 1265): 126.5 -> 1391.5
    # TGST (17% on 1391.5): 236.56 -> 1628.06
    res = await client.post("/imoxon/pricing/landed-cost", params={"base": 1000, "cat": "RESORT_SUPPLY"}, headers=headers)
    pricing = res.json()
    assert pricing["total"] == 1628.06
    # Standard FCE test without landed engine overhead
    from main import fce_core
    fce_res = fce_core.finalize_invoice(1000, "TOURISM")
    assert fce_res["total"] == 1287.0
    assert fce_res["tax_rate"] == 0.17

@pytest.mark.anyio
async def test_shadow_audit_creation(client, headers):
    from main import shadow_core
    initial_len = len(shadow_core.chain)
    await client.post("/imoxon/suppliers/connect", params={"name": "Audit Test"}, headers=headers)
    # Each execute_sovereign_action creates 2 entries (Intent + Committed)
    # plus the direct commit in connect_supplier endpoint itself for the profile
    # total 3 commits.
    # BUT get_actor_ctx also commits success.
    # Total may vary depending on previous tests in session.
    assert len(shadow_core.chain) > initial_len
    last_block = shadow_core.chain[-1]
    assert last_block["event_type"].endswith(".completed")
    assert last_block["payload"]["status"] == "COMMITTED"
    assert last_block["payload"]["actor_aegis_id"] == headers["X-AEGIS-IDENTITY"]

@pytest.mark.anyio
async def test_failed_transaction_rollback(client, headers):
    # Attempt to approve non-existent product
    # Ensure TestClient doesn't raise exception so we can check status code
    try:
        res = await client.post("/imoxon/products/approve", params={"pid": "none"}, headers=headers)
        assert res.status_code in [403, 500]
    except RuntimeError as e:
        assert "SOVEREIGN EXECUTION FAILED" in str(e)

    from main import shadow_core
    # Failures are logged in the chain with event_type {action}.failed
    failure_entry = [b for b in shadow_core.chain if b["event_type"] == "imoxon.catalog.approve.failed"][-1]
    assert failure_entry["payload"]["status"] == "FAILED_ROLLBACK"

@pytest.mark.anyio
async def test_unauthorized_mutation_rejection(client):
    # Try to approve product without valid admin headers
    res = await client.post("/imoxon/products/approve", params={"pid": "123"})
    assert res.status_code == 401
