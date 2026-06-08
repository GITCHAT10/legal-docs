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
    # Verify the admin so they can perform restricted actions
    await client.post("/imoxon/aegis/identity/verify", params={"identity_id": actor_id, "verifier_id": "SYSTEM"})
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
    from mnos.modules.finance.fce import FCEEngine
    from decimal import Decimal
    fce = FCEEngine()
    # 1000 + 10% SC = 1100
    # 1100 + 17% TGST = 1100 + 187 = 1287
    res = fce.calculate_local_order(Decimal("1000.00"), "TOURISM")
    assert res["total"] == 1287.0

@pytest.mark.anyio
async def test_shadow_audit_creation(client, headers):
    # Any commerce action should create shadow logs
    res = await client.post("/imoxon/orders/create", json={"items": [], "amount": 100}, headers=headers)
    assert res.status_code == 200

    from main import shadow_core
    # Verify chain grew
    assert len(shadow_core.chain) > 0
    # Verify last event was a completion
    assert "completed" in shadow_core.chain[-1]["event_type"]

@pytest.mark.anyio
async def test_failed_transaction_rollback(client, headers):
    from main import shadow_core
    len(shadow_core.chain)

    # Try an action that will fail business logic
    # Catalog approve with invalid ID
    res = await client.post("/imoxon/products/approve", params={"pid": "invalid-id"}, headers=headers)
    assert res.status_code == 500

    # Verify failure log in shadow
    assert "failed" in shadow_core.chain[-1]["event_type"]

@pytest.mark.anyio
async def test_unauthorized_mutation_rejection(client):
    # Try to approve product without valid signature headers
    res = await client.post("/imoxon/products/approve", params={"pid": "123"})
    assert res.status_code == 401
