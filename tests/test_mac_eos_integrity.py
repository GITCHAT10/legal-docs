import pytest
from fastapi.testclient import TestClient
from main import app, shadow_core, identity_gateway, iluvia_orchestrator, guard, identity_core, gateway, shield_edge
from mnos.shared.exceptions import ExecutionValidationError
import os

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_system_state():
    """Reset rate limits and state between tests to prevent 429 interference."""
    gateway.rate_limits = {}
    shield_edge.rate_store = {}
    yield

@pytest.fixture
def auth_headers():
    # Setup real identity in AEGIS
    with guard.sovereign_context({"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}):
        uid = identity_core.create_profile({"full_name": "Hardened Staff", "profile_type": "staff"})
        did = identity_core.bind_device(uid, {"fingerprint": "hard-dev-01"})
        identity_core.verify_identity(uid, "system")

    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-ISLAND-ID": "GLOBAL"
    }

def test_confirm_real_world_fails_for_unknown_order(auth_headers):
    """Integrity: Rejects confirmation of non-existent orders"""
    # 1. Attempt confirmation for unknown ID
    response = client.post(
        "/bubble/execution/confirm?order_id=non_existent_123",
        json={"type": "QR_SCAN", "valid": True},
        headers=auth_headers
    )

    # Verify rejection
    # Re-raised as 400 now via exception handler
    assert response.status_code == 400
    assert "ORDER_NOT_FOUND" in response.json()["detail"]

    # 2. Verify NO SHADOW write for this order occurred (besides the general failed attempt log)
    events = [b["event_type"] for b in shadow_core.chain]
    assert "execution.confirmed" not in events

def test_confirm_real_world_success_path(auth_headers):
    """Integrity: Valid order -> success path -> SHADOW write"""
    order_id = "ORD-VALID-101"
    iluvia_orchestrator.set_order_state(order_id, "EXECUTION_PENDING", "PROCUREMENT")

    response = client.post(
        f"/bubble/execution/confirm?order_id={order_id}",
        json={"type": "QR_SCAN", "valid": True},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json() is True

    # Verify SHADOW write
    events = [b["event_type"] for b in shadow_core.chain]
    assert "execution.confirmed" in events

def test_session_auth_allowed_on_user_paths(auth_headers):
    """Auth: Valid session token must pass for Bubble and ExMail"""
    session_id = "SESS-USER-456"
    identity_gateway.sessions[session_id] = {
        "identity_id": auth_headers["X-AEGIS-IDENTITY"],
        "device_id": auth_headers["X-AEGIS-DEVICE"],
        "role": "admin",
        "realm": "API_DIRECT"
    }

    # Test Bubble (Chat)
    resp1 = client.post(
        "/bubble/chat/message?message=test",
        headers={"X-AEGIS-SESSION": session_id, "X-ISLAND-ID": "GLOBAL"}
    )
    assert resp1.status_code == 200

    # Test ExMail
    resp2 = client.post(
        "/exmail/ingest?channel=whatsapp",
        json={"sender": "g1", "content": "hi"},
        headers={"X-AEGIS-SESSION": session_id, "X-ISLAND-ID": "GLOBAL"}
    )
    assert resp2.status_code == 200

def test_missing_auth_fails_closed():
    """Auth: Requests without any identity or session must fail"""
    response = client.post("/bubble/chat/message?message=test", headers={"X-ISLAND-ID": "GLOBAL"})
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]

def test_strict_path_rejects_session_only(auth_headers):
    """Auth: Strict paths must fail if device binding (headers) is missing"""
    session_id = "SESS-STRICT-789"
    identity_gateway.sessions[session_id] = {
        "identity_id": "any", "role": "admin", "realm": "API_DIRECT"
    }

    # /imoxon/orders/create is STRICT
    response = client.post(
        "/imoxon/orders/create",
        json={"amount": 100, "items": []},
        headers={"X-AEGIS-SESSION": session_id, "X-ISLAND-ID": "GLOBAL"}
    )
    assert response.status_code == 403
    assert "Strict endpoint requires" in response.json()["detail"]
