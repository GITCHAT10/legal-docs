import pytest
from httpx import ASGITransport, AsyncClient
from main import app, shadow_core, iluvia_orchestrator, guard, identity_core

@pytest.mark.anyio
async def test_confirm_real_world_fails_for_unknown_order():
    """
    Priority 1: Unknown order_id must fail and NOT create SHADOW completion.
    """
    # 1. Clear shadow chain for clean test (optional but good for precise counting)
    initial_count = len(shadow_core.chain)

    # 2. Preparation: Admin context for the call
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}

    # 3. Call confirm_real_world with fake ID
    # Use ASGITransport to test the exception mapping to 400
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Confirming execution via API to check error handling
        infra_headers = {
            "X-AEGIS-IDENTITY": "infra_node",
            "X-AEGIS-DEVICE": "trusted_hw",
            "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_infra_node"
        }
        # Register infra node first
        with guard.sovereign_context(SYSTEM_CTX):
            identity_core.profiles["infra_node"] = {"profile_type": "admin", "verification_status": "verified"}
            identity_core.devices["trusted_hw"] = {"identity_id": "infra_node"}

        confirm_payload = {"type": "QR_SCAN", "valid": True}
        res = await ac.post("/bubble/execution/confirm?order_id=FAKE-ID-999", json=confirm_payload, headers=infra_headers)

        assert res.status_code == 400
        assert "ORDER_NOT_FOUND" in res.text

    # 4. Verify SHADOW has no "execution.confirmed" for this fake order
    events = [b["event_type"] for b in shadow_core.chain[initial_count:]]
    assert "execution.confirmed" not in events

@pytest.mark.anyio
async def test_confirm_real_world_success_path():
    """
    Priority 1: Valid order must succeed.
    """
    initial_count = len(shadow_core.chain)
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}

    # 1. Create a "truth" order in the repo
    order_id = "VALID-ORDER-123"
    iluvia_orchestrator.set_order_state(order_id, "EXECUTION_PENDING", "PROCUREMENT")

    # 2. Confirm it
    with guard.sovereign_context(SYSTEM_CTX):
        res = iluvia_orchestrator.confirm_real_world(order_id, {"type": "QR_SCAN", "valid": True})

    assert res is True

    # 3. Verify SHADOW commit
    events = [b["event_type"] for b in shadow_core.chain[initial_count:]]
    assert "execution.confirmed" in events

@pytest.mark.anyio
async def test_session_auth_allowed_on_user_paths():
    """
    Priority 2: /bubble and /exmail support session auth.
    """
    # 1. Setup session in Aegis
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with guard.sovereign_context(SYSTEM_CTX):
        guest_id = identity_core.create_profile({"full_name": "Test Guest", "profile_type": "guest"})
        from main import identity_gateway
        login_res = identity_gateway.login("D2C", "PHONE_OTP", {"phone": "999", "name": "Test Guest"})
        session_id = login_res["session_id"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 2. Call /bubble/chat/message with session header
        headers = {"X-AEGIS-SESSION": session_id}
        res = await ac.post("/bubble/chat/message?message=hello", headers=headers)

        # 3. Should NOT be 403/401 if session is valid
        assert res.status_code == 200

@pytest.mark.anyio
async def test_missing_auth_fails_closed():
    """
    Priority 2: NO valid identity/session -> NO access.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Call protected route without headers
        res = await ac.post("/bubble/chat/message?message=hello")
        assert res.status_code in [401, 403]

@pytest.mark.anyio
async def test_strict_path_rejects_session_only():
    """
    Priority 2: Strict paths (finance/supply) must still require Identity + Device.
    """
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}
    with guard.sovereign_context(SYSTEM_CTX):
        guest_id = identity_core.create_profile({"full_name": "Test Guest", "profile_type": "guest"})
        from main import identity_gateway
        login_res = identity_gateway.login("D2C", "PHONE_OTP", {"phone": "999", "name": "Test Guest"})
        session_id = login_res["session_id"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # /supply/products/import (mapped to imoxon)
        headers = {"X-AEGIS-SESSION": session_id}
        res = await ac.post("/imoxon/products/import?sid=S1", json={}, headers=headers)

        # Middleware should block /imoxon (STRICT) if session-only
        assert res.status_code == 403
