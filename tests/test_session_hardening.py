import pytest
import uuid
from fastapi.testclient import TestClient
from main import app, identity_core, identity_gateway, mars_unified

client = TestClient(app)

@pytest.fixture
def session_user():
    # Use a unique name to avoid collisions
    unique_name = f"Session User {uuid.uuid4().hex[:6]}"
    # 1. Create Identity
    uid = identity_core.create_profile({"full_name": unique_name, "profile_type": "admin"})
    identity_core.verify_identity(uid, "TEST")

    # 2. Bind Device
    did = identity_core.bind_device(uid, {"fingerprint": "secure-session-device"})

    # 3. Create Session via Login
    login_res = identity_gateway.login("ISLAND_GM", "PHONE_OTP", {"id": unique_name})
    session_id = login_res["session_id"]

    return {"uid": uid, "did": did, "sid": session_id}

def test_session_auth_without_device_rejected_for_mutating_action(session_user):
    """Codex P1 Fix: Session auth must still provide valid device for write actions."""
    headers = {"X-AEGIS-SESSION": session_user["sid"]}

    # Try a mutating action (campaign creation)
    payload = {"code": f"HACK-{uuid.uuid4().hex[:4]}", "discount": 99}
    resp = client.post("/imoxon/coupon/campaign", json=payload, headers=headers)

    # Should be rejected because device_id is missing in actor context
    assert resp.status_code == 403
    # Flexible check for the detail message as it might be prefixed
    assert "FAIL CLOSED: Missing" in resp.json()["detail"]
    assert "Device Binding" in resp.json()["detail"]

def test_session_auth_with_invalid_device_rejected(session_user):
    """Device provided with session must belong to the user."""
    # Rogue device
    rogue_did = str(uuid.uuid4())

    headers = {
        "X-AEGIS-SESSION": session_user["sid"],
        "X-AEGIS-DEVICE": rogue_did
    }

    resp = client.post("/imoxon/coupon/campaign", json={}, headers=headers)
    assert resp.status_code == 403
    assert "DEVICE_BINDING_INVALID" in resp.json()["detail"]

def test_session_auth_with_valid_device_accepted(session_user):
    """Session + Valid Bound Device = Success."""
    headers = {
        "X-AEGIS-SESSION": session_user["sid"],
        "X-AEGIS-DEVICE": session_user["did"]
    }

    payload = {"code": f"SECURE-{uuid.uuid4().hex[:4]}", "discount": 10}
    resp = client.post("/imoxon/coupon/campaign", json=payload, headers=headers)
    assert resp.status_code == 200

def test_read_only_session_without_device_allowed(session_user):
    """Read-only session requests should not globally require device headers unless doctrine says so."""
    headers = {"X-AEGIS-SESSION": session_user["sid"]}

    # Standard read-only endpoint (catalog)
    resp = client.get("/imoxon/catalog", headers=headers)
    assert resp.status_code == 200

def test_direct_auth_still_works(admin_headers):
    """Ensure we didn't break existing direct handshake path."""
    payload = {"code": f"DIRECT-{uuid.uuid4().hex[:4]}", "discount": 5}
    resp = client.post("/imoxon/coupon/campaign", json=payload, headers=admin_headers)
    assert resp.status_code == 200
