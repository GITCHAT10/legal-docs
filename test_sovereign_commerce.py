import pytest
import asyncio
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

@pytest.mark.anyio
async def test_unsigned_request_rejected(client):
    res = await client.post("/commerce/orders/create", json={})
    assert res.status_code == 403
    assert "Missing Actor Identity" in res.json()["detail"]

@pytest.mark.anyio
async def test_missing_device_rejected(client):
    headers = {"X-AEGIS-IDENTITY": "actor-123"}
    res = await client.post("/commerce/orders/create", json={}, headers=headers)
    assert res.status_code == 403
    assert "Missing Device Binding" in res.json()["detail"]

@pytest.mark.anyio
async def test_vendor_kyc_blocked(client):
    res = await client.post("/aegis/identity/create", json={"full_name": "Adam", "profile_type": "staff"})
    actor_id = res.json()["identity_id"]
    await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "dev-1"})
    headers = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": "dev-1"}
    res = await client.post("/commerce/orders/create", json={"vendor_id": "bad-vendor", "amount": 100}, headers=headers)
    assert res.status_code == 500
    assert "Vendor not approved" in res.json()["detail"]

@pytest.mark.anyio
async def test_milestone_release_only_on_verified_proof(client):
    res = await client.post("/aegis/identity/create", json={"full_name": "Adam", "profile_type": "staff"})
    actor_id = res.json()["identity_id"]
    await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "dev-1"})
    headers = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": "dev-1"}
    res = await client.post("/commerce/payouts/release", params={"milestone": "AWARD", "ref_id": "rfp_1", "total_amount": 1000}, headers=headers)
    assert res.status_code == 500
    assert "No verified SHADOW proof" in res.json()["detail"]

@pytest.mark.anyio
async def test_milestone_release_success_after_proof(client):
    res = await client.post("/aegis/identity/create", json={"full_name": "Adam", "profile_type": "staff"})
    actor_id = res.json()["identity_id"]
    await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "dev-1"})
    headers = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": "dev-1"}

    # 1. Record Proof
    await client.post("/commerce/milestones/verify", json={"milestone": "AWARD", "ref_id": "rfp_1", "timestamp": "now"}, headers=headers)

    # 2. Release Payout
    res = await client.post("/commerce/payouts/release", params={"milestone": "AWARD", "ref_id": "rfp_1", "total_amount": 1000}, headers=headers)
    assert res.status_code == 200
    assert res.json()["release_amount"] == 100.0

@pytest.mark.anyio
async def test_maldives_billing_math(client):
    res = await client.post("/aegis/identity/create", json={"full_name": "Adam", "profile_type": "staff"})
    actor_id = res.json()["identity_id"]
    await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "dev-1"})
    headers = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": "dev-1"}
    await client.post("/commerce/vendors/approve", json={"did": "vend-1", "business_name": "Stelco"}, headers=headers)
    res = await client.post("/commerce/orders/create", json={"vendor_id": "vend-1", "amount": 1000}, headers=headers)
    order = res.json()
    pricing = order["pricing"]
    assert pricing["base"] == 1000.0
    assert pricing["service_charge"] == 100.0
    assert pricing["subtotal"] == 1100.0
    assert pricing["total"] == 1188.0

@pytest.mark.anyio
async def test_direct_event_publish_blocked():
    from mnos.modules.events.bus import EventBus
    bus = EventBus()
    with pytest.raises(PermissionError) as exc:
        bus.publish("test.event", {})
    assert "Direct event publish blocked" in str(exc.value)

@pytest.mark.anyio
async def test_direct_shadow_commit_blocked():
    from mnos.modules.shadow.ledger import ShadowLedger
    ledger = ShadowLedger()
    with pytest.raises(PermissionError) as exc:
        ledger.commit("test.event", {})
    assert "Direct SHADOW commit blocked" in str(exc.value)

@pytest.mark.anyio
async def test_atomic_rollback_on_failure(client):
    # vector: If business logic fails, check if we have a failure log in shadow
    # and the state isn't partial (though in-memory is harder to verify partiality)
    res = await client.post("/aegis/identity/create", json={"full_name": "Adam", "profile_type": "staff"})
    actor_id = res.json()["identity_id"]
    await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "dev-1"})
    headers = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": "dev-1"}

    # Attempt payout without proof triggers error in engine
    res = await client.post("/commerce/payouts/release", params={"milestone": "AWARD", "ref_id": "err_1", "total_amount": 1000}, headers=headers)
    assert res.status_code == 500

    # Verify SHADOW has the failure entry
    # Since we use a singleton shadow_core in main.py, we can check it if we import it
    from main import shadow_core
    last_block = shadow_core.get_block(len(shadow_core.chain) - 1)
    assert last_block["data"]["event_type"] == "imoxon.payment.release.failed"
    assert last_block["data"]["payload"]["status"] == "FAILED_ROLLBACK"

@pytest.mark.anyio
async def test_refund_reversal_logic(client):
    from mnos.modules.finance.fce import FCEEngine
    fce = FCEEngine()
    invoice = fce.finalize_invoice(1000, "RETAIL")
    refund = fce.calculate_refund(invoice)

    assert refund["total"] == -1188.0
    assert refund["type"] == "REVERSAL"
