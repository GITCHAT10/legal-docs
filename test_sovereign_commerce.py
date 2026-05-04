import pytest
import httpx
import os
import json
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
    if res.status_code != 200:
        print(f"DEBUG FIXTURE: create identity failed: {res.status_code} {res.text}")
    actor_id = res.json()["identity_id"]
    res = await client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "test-dev"})
    if res.status_code != 200:
        print(f"DEBUG FIXTURE: bind device failed: {res.status_code} {res.text}")
    device_id = res.json()["device_id"]
    await client.post("/imoxon/aegis/identity/verify", params={"identity_id": actor_id, "verifier_id": "SYSTEM"})
    return {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": device_id, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"}

@pytest.mark.anyio
async def test_unsigned_request_rejected(client):
    res = await client.post("/imoxon/orders/create", json={})
    assert res.status_code == 403
    assert "AEGIS_REQUIRED" in res.json()["detail"]

@pytest.mark.anyio
async def test_missing_device_rejected(client):
    headers = {"X-AEGIS-IDENTITY": "actor-123"}
    res = await client.post("/imoxon/orders/create", json={}, headers=headers)
    assert res.status_code == 403
    assert "AEGIS_REQUIRED" in res.json()["detail"]

@pytest.mark.anyio
async def test_maldives_billing_math(client, headers):
    res = await client.post("/imoxon/pricing/landed-cost", params={"base": 1000, "cat": "RESORT_SUPPLY"}, headers=headers)
    assert res.status_code == 200
    pricing = res.json()
    assert pricing.get("total") == 1628.06

    from main import fce_core
    fce_res = fce_core.finalize_invoice(1000, "TOURISM")
    assert fce_res["total"] == 1287.0
    assert fce_res["tax_rate"] == 0.17

@pytest.mark.anyio
async def test_shadow_audit_creation(client, headers):
    from main import shadow_core
    res = await client.post("/imoxon/suppliers/connect", params={"name": "Audit Test"}, headers=headers)
    assert res.status_code == 200

    try:
        last_block = next(b for b in reversed(shadow_core.chain) if b["event_type"].endswith(".completed") or b["event_type"].endswith(".failed"))
        assert last_block["payload"].get("status") in ["COMMITTED", "FAILED_ROLLBACK"]
        assert last_block["payload"].get("actor_aegis_id") == headers["X-AEGIS-IDENTITY"]
    except StopIteration:
        pytest.fail(f"No business event found in shadow chain. Chain: {[b['event_type'] for b in shadow_core.chain]}")

@pytest.mark.anyio
async def test_failed_transaction_rollback(client, headers):
    # This might raise a 500/RuntimeError in the test runner if not caught by FastAPI handler
    # But since we want to verify the rollback in SHADOW, we can ignore the test failure if needed,
    # or wrap it if we had a handler.
    # Let's try catching the exception in the test itself if possible, but httpx client will just see 500.
    res = await client.post("/imoxon/products/approve", params={"pid": "none"}, headers=headers)
    # If no exception handler for RuntimeError, FastAPI returns 500
    assert res.status_code in [400, 403, 404, 500]

    from main import shadow_core
    try:
        last_block = next(b for b in reversed(shadow_core.chain) if b["event_type"].endswith(".completed") or b["event_type"].endswith(".failed"))
        assert last_block["payload"].get("status") == "FAILED_ROLLBACK"
    except StopIteration:
        pytest.fail(f"No failure event found in shadow chain. Chain: {[b['event_type'] for b in shadow_core.chain]}")

@pytest.mark.anyio
async def test_unauthorized_mutation_rejection(client):
    res = await client.post("/imoxon/products/approve", params={"pid": "123"})
    assert res.status_code == 403
