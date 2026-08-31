import httpx
import pytest
from httpx import ASGITransport

from main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def actor_headers(client):
    created = await client.post(
        "/imoxon/aegis/identity/create",
        json={"full_name": "Test Admin", "profile_type": "admin"},
    )
    assert created.status_code == 200, created.text
    actor_id = created.json()["identity_id"]

    bound = await client.post(
        "/imoxon/aegis/identity/device/bind",
        params={"identity_id": actor_id},
        json={"fingerprint": "test-dev"},
    )
    assert bound.status_code == 200, bound.text
    device_id = bound.json()["device_id"]

    return {
        "X-AEGIS-IDENTITY": actor_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}",
    }


@pytest.mark.anyio
async def test_unsigned_request_rejected(client):
    res = await client.post("/imoxon/orders/create", json={})
    assert res.status_code == 401
    assert "Missing Identity, Device or Signature" in res.json()["detail"]


@pytest.mark.anyio
async def test_missing_device_rejected(client, actor_headers):
    headers = {
        "X-AEGIS-IDENTITY": actor_headers["X-AEGIS-IDENTITY"],
        "X-AEGIS-SIGNATURE": actor_headers["X-AEGIS-SIGNATURE"],
    }
    res = await client.post("/imoxon/orders/create", json={}, headers=headers)
    assert res.status_code == 401
    assert "Missing Identity, Device or Signature" in res.json()["detail"]


@pytest.mark.anyio
async def test_authenticated_procurement_and_maldives_billing(client, actor_headers):
    res = await client.post(
        "/imoxon/orders/create",
        json={"items": [{"sku": "TEST-1", "qty": 1}], "amount": 1000},
        headers=actor_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "CREATED"

    from main import fce_core

    fce_res = fce_core.finalize_invoice(1000, "TOURISM")
    assert fce_res["total"] == 1287.0
    assert fce_res["tax_rate"] == 0.17


@pytest.mark.anyio
async def test_shadow_audit_creation(client, actor_headers):
    from main import shadow_core

    initial_len = len(shadow_core.chain)
    res = await client.post(
        "/imoxon/suppliers/connect",
        params={"name": "Audit Test"},
        headers=actor_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "CONNECTED"

    new_blocks = shadow_core.chain[initial_len:]
    event_types = [block["event_type"] for block in new_blocks]

    assert "imoxon.supplier.connect.intent" in event_types
    assert "identity.created" in event_types
    assert "imoxon.supplier.connect.completed" in event_types

    completed = next(
        block for block in reversed(new_blocks)
        if block["event_type"] == "imoxon.supplier.connect.completed"
    )
    assert completed["payload"]["status"] == "COMMITTED"
    assert completed["payload"]["actor_aegis_id"] == actor_headers["X-AEGIS-IDENTITY"]


@pytest.mark.anyio
async def test_failed_transaction_rollback(client, actor_headers):
    from main import shadow_core

    res = await client.post(
        "/imoxon/products/approve",
        params={"pid": "none"},
        headers=actor_headers,
    )
    assert res.status_code == 500

    last_block = shadow_core.chain[-1]
    assert last_block["event_type"] == "imoxon.catalog.approve.failed"
    assert last_block["payload"]["status"] == "FAILED_ROLLBACK"


@pytest.mark.anyio
async def test_invalid_signature_rejected(client, actor_headers):
    headers = dict(actor_headers)
    headers["X-AEGIS-SIGNATURE"] = "INVALID"
    res = await client.post("/imoxon/orders/create", json={}, headers=headers)
    assert res.status_code == 403
    assert "HANDSHAKE_FAILED" in res.json()["detail"]
