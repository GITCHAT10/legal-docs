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
    await client.post("/imoxon/aegis/identity/verify", params={"identity_id": actor_id, "verifier_id": "SYSTEM"})
    res = await client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "test-dev"})
    device_id = res.json()["device_id"]
    return {
        "X-AEGIS-IDENTITY": actor_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"
    }

@pytest.mark.anyio
async def test_high_score_outreach_returns_approval_id(client, headers):
    # Priority A contact
    data = {"contact_id": "VIP-001", "priority": "A", "lead_score": "15", "full_name": "VIP Client", "email": "vip@test.com"}
    res = await client.post("/prestige/staging/outreach/process", json=data, headers=headers)
    assert res.status_code == 200
    assert "approval_id" in res.json()
    assert res.json()["status"] == "pending_human_approval"

@pytest.mark.anyio
async def test_approval_endpoint_accepts_approval_id(client, headers):
    # 1. Queue
    data = {"contact_id": "VIP-002", "priority": "A", "lead_score": "15"}
    res = await client.post("/prestige/staging/outreach/process", json=data, headers=headers)
    approval_id = res.json()["approval_id"]

    # 2. Approve
    res = await client.post("/prestige/staging/outreach/approve", json={"approval_id": approval_id}, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "sent"

@pytest.mark.anyio
async def test_approval_id_cannot_be_reused(client, headers):
    # 1. Queue
    data = {"contact_id": "VIP-003", "priority": "A", "lead_score": "15"}
    res = await client.post("/prestige/staging/outreach/process", json=data, headers=headers)
    approval_id = res.json()["approval_id"]

    # 2. Approve once
    await client.post("/prestige/staging/outreach/approve", json={"approval_id": approval_id}, headers=headers)

    # 3. Approve again should fail
    res = await client.post("/prestige/staging/outreach/approve", json={"approval_id": approval_id}, headers=headers)
    assert res.status_code == 500 # RuntimeError from ExecutionGuard
    assert "already processed" in res.json()["detail"]

@pytest.mark.anyio
async def test_malformed_actor_context_fails_closed(client):
    # No headers -> Missing Identity or Device
    data = {"contact_id": "VIP-004", "priority": "A", "lead_score": "15"}
    res = await client.post("/prestige/staging/outreach/process", json=data)
    assert res.status_code == 401 # AEGIS required

@pytest.mark.anyio
async def test_empty_hotel_inventory_returns_no_availability(client, headers):
    # Inquiry that returns no hotels (mocked)
    # Since our mock currently returns fixed results, let's add a condition or use a fake location
    # For this test, I will temporarily modify the adapter to return empty if location is 'nowhere'
    data = {"text": "book something", "location": "nowhere", "guests": 1, "nights": 1}

    # We need to make sure the adapter returns empty.
    # Current DirectMaldivesAdapter always returns 2 hotels.
    # I'll rely on the logic being correct if I can force empty.

    from main import prestige_sourcing
    # Mock search_hotels to return empty
    original_search = prestige_sourcing.search_hotels
    async def mock_empty(query): return []
    prestige_sourcing.search_hotels = mock_empty

    try:
        res = await client.post("/prestige/staging/workflow/luxury-package", json=data, headers=headers)
        assert res.status_code == 200
        assert res.json()["status"] == "no_availability"
        assert res.json()["recovery_required"] is True
    finally:
        prestige_sourcing.search_hotels = original_search

@pytest.mark.anyio
async def test_no_availability_event_is_shadow_sealed(client, headers):
    from main import shadow_core, prestige_sourcing
    len(shadow_core.chain)

    async def mock_empty(query): return []
    original_search = prestige_sourcing.search_hotels
    prestige_sourcing.search_hotels = mock_empty

    try:
        data = {"text": "nothing", "location": "void"}
        await client.post("/prestige/staging/workflow/luxury-package", json=data, headers=headers)

        # Verify event in SHADOW
        assert any(e["event_type"] == "prestige.package.no_availability.completed" for e in shadow_core.chain)
    finally:
        prestige_sourcing.search_hotels = original_search
