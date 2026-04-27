import pytest
from fastapi.testclient import TestClient
from main import app, shadow_core, identity_gateway, iluvia_orchestrator, guard, identity_core

client = TestClient(app)

@pytest.fixture
def auth_headers():
    # Setup real identity in AEGIS
    with guard.sovereign_context({"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}):
        uid = identity_core.create_profile({"full_name": "Integrity Staff", "profile_type": "staff"})
        did = identity_core.bind_device(uid, {"fingerprint": "int-dev-01"})
        identity_core.verify_identity(uid, "system")

    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-ISLAND-ID": "GLOBAL"
    }

def test_fake_order_rejected(auth_headers):
    """P1: System must reject confirmation of non-existent orders"""
    response = client.post(
        "/bubble/execution/confirm?order_id=fake_123",
        json={"type": "QR_SCAN", "valid": True},
        headers=auth_headers
    )
    assert response.status_code == 500 # Guard re-raises ValueError
    assert "ORDER_NOT_FOUND" in response.json()["detail"]

    # Verify SHADOW logged the invalid attempt
    events = [b["event_type"] for b in shadow_core.chain]
    assert "shield.invalid_confirm_attempt" in events

def test_session_auth_allowed_on_dual_paths(auth_headers):
    """P1: Dual-auth paths must accept valid session tokens"""
    session_id = "SESS-VALID-99"
    identity_gateway.sessions[session_id] = {
        "identity_id": auth_headers["X-AEGIS-IDENTITY"],
        "role": "admin",
        "realm": "API_DIRECT",
        "device_id": auth_headers["X-AEGIS-DEVICE"]
    }

    response = client.post(
        "/bubble/chat/message?message=hello",
        headers={"X-AEGIS-SESSION": session_id, "X-ISLAND-ID": "GLOBAL"}
    )
    assert response.status_code == 200

def test_strict_path_rejects_session_auth(auth_headers):
    """P1: Strict paths must reject session-only auth"""
    session_id = "SESS-VALID-99"
    identity_gateway.sessions[session_id] = {
        "identity_id": auth_headers["X-AEGIS-IDENTITY"],
        "role": "admin",
        "realm": "API_DIRECT",
        "device_id": auth_headers["X-AEGIS-DEVICE"]
    }

    # /imoxon/orders/create is in STRICT_GUARD_PATHS
    # Note: main.py uses @app.post("/imoxon/orders/create")
    response = client.post(
        "/imoxon/orders/create",
        json={"amount": 100, "items": []},
        headers={"X-AEGIS-SESSION": session_id, "X-ISLAND-ID": "GLOBAL"}
    )
    assert response.status_code == 403
    assert "Strict endpoint requires" in response.json()["detail"]

def test_invariant_no_confirm_without_order(auth_headers):
    """System-level invariant: cannot confirm non-existent order"""
    order_id = "ghost_order"

    # 1. Attempt confirmation
    response = client.post(
        f"/bubble/execution/confirm?order_id={order_id}",
        json={"type": "QR_SCAN", "valid": True},
        headers=auth_headers
    )
    assert response.status_code == 500
    assert "ORDER_NOT_FOUND" in response.json()["detail"]

    # 2. Verify SHADOW has failure rollback log
    events = [b["event_type"] for b in shadow_core.chain]
    assert "bubble.execution.confirm.failed" in events
    # And NO success log
    assert "bubble.execution.confirm.completed" not in events
