import pytest
import httpx
from main import app, identity_core, shadow_core

@pytest.mark.anyio
async def test_unknown_identity_returns_401():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Unknown identity
        headers = {"X-AEGIS-IDENTITY": "unknown-actor"}
        response = await client.get("/upos/enterprise/dashboard", headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "INVALID_IDENTITY"

@pytest.mark.anyio
async def test_missing_profile_never_becomes_guest():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # If header provided but unknown, should NOT fall back to guest
        headers = {"X-AEGIS-IDENTITY": "non-existent-profile"}
        response = await client.get("/upos/enterprise/dashboard", headers=headers)
        assert response.status_code == 401
        # Confirm it's not guest by checking if it returned 200 (guest might have limited access)
        assert response.status_code != 200

@pytest.mark.anyio
async def test_mismatched_device_returns_403():
    # Setup identity and device
    identity_id = identity_core.create_profile({"profile_type": "admin", "verification_status": "verified"})
    other_identity = identity_core.create_profile({"profile_type": "staff", "verification_status": "verified"})
    device_id = identity_core.bind_device(identity_id, {"device_type": "mobile"})

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Match identity but wrong device (device bound to identity_id, not other_identity)
        headers = {
            "X-AEGIS-IDENTITY": other_identity,
            "X-AEGIS-DEVICE": device_id
        }
        response = await client.get("/upos/enterprise/dashboard", headers=headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "DEVICE_BINDING_INVALID"

@pytest.mark.anyio
async def test_invalid_signature_returns_403():
    identity_id = identity_core.create_profile({"profile_type": "admin", "verification_status": "verified"})
    device_id = identity_core.bind_device(identity_id, {"device_type": "mobile"})

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        headers = {
            "X-AEGIS-IDENTITY": identity_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": "INVALID"
        }
        response = await client.get("/upos/enterprise/dashboard", headers=headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "HANDSHAKE_FAILED"

@pytest.mark.anyio
async def test_apollo_missing_actor_ctx_logs_failure_and_continues():
    # Setup
    identity_id = identity_core.create_profile({"profile_type": "admin", "verification_status": "verified"})
    device_id = identity_core.bind_device(identity_id, {"device_type": "mobile"})

    events = [
        {"type": "valid.event", "actor_ctx": {"identity_id": identity_id}, "payload": {"data": "ok"}},
        {"type": "malformed.event", "payload": {"data": "bad"}}, # Missing actor_ctx
        {"type": "valid.event.2", "actor_ctx": {"identity_id": identity_id}, "payload": {"data": "ok2"}}
    ]

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        headers = {
            "X-AEGIS-IDENTITY": identity_id,
            "X-AEGIS-DEVICE": device_id
        }
        response = await client.post("/upos/apollo/sync?tenant_id=T1", json=events, headers=headers)
        assert response.status_code == 200
        data = response.json()
        # synced_count should be 2 because valid.event and valid.event.2 succeeded
        assert data["synced_count"] == 2

        # Verify failure logged to shadow
        # We check shadow logs for 'apollo.sync.failure'
        found_failure = False
        for block in shadow_core.chain:
            if block.get("event_type") == "apollo.sync.failure":
                found_failure = True
                break
        assert found_failure

@pytest.mark.anyio
async def test_no_shadow_write_without_authorized_actor_ctx():
    # Attempt direct write to shadow_core without being in an ExecutionGuard context
    with pytest.raises(PermissionError) as exc:
        shadow_core.commit("test.event", "unknown", {"data": "secret"})
    assert "Unauthorized direct write to SHADOW Ledger blocked" in str(exc.value)

@pytest.mark.anyio
async def test_upos_invoice_requires_fce_calculation():
    identity_id = identity_core.create_profile({"profile_type": "admin", "verification_status": "verified"})
    device_id = identity_core.bind_device(identity_id, {"device_type": "mobile"})

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        headers = {
            "X-AEGIS-IDENTITY": identity_id,
            "X-AEGIS-DEVICE": device_id
        }
        # Amount 1000 should result in 1287 (1000 + 10% SC + 17% TGST)
        # Category must be RESORT_SUPPLY or TOURISM for 17% tax
        response = await client.post("/upos/api/v1/invoices/create", json={"amount": 1000, "category": "RESORT_SUPPLY"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["pricing"]["total"] == 1287.0
