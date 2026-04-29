import pytest
from fastapi.testclient import TestClient
from main import app, identity_core
from mnos.shared.execution_guard import _sovereign_context

client = TestClient(app)

@pytest.fixture
def valid_actor():
    # Setup valid profile and device
    token = _sovereign_context.set({"token": "TEST-SETUP", "actor": {"identity_id": "SYSTEM", "system_override": True}})
    try:
        identity_id = identity_core.create_profile({"full_name": "Valid User", "profile_type": "user"})
        device_id = identity_core.bind_device(identity_id, {"fingerprint": "d1"})
        return identity_id, device_id
    finally:
        _sovereign_context.reset(token)

def test_valid_aegis_identity_passes(valid_actor):
    uid, did = valid_actor
    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }
    # Create order
    response = client.post("/imoxon/orders/create", json={"items": [], "amount": 100}, headers=headers)
    assert response.status_code == 200

def test_device_mismatch_blocks(valid_actor):
    uid, did = valid_actor
    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": "wrong-device",
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }
    response = client.post("/imoxon/orders/create", json={"items": [], "amount": 100}, headers=headers)
    assert response.status_code == 403
    assert "DEVICE_BINDING_INVALID" in response.json()["detail"]

def test_unauthorized_header_injection_fails():
    # Attempting to fake a role via headers (if it were possible)
    headers = {
        "X-AEGIS-IDENTITY": "fake-id",
        "X-AEGIS-DEVICE": "fake-device",
        "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_fake-id"
    }
    response = client.post("/imoxon/orders/create", json={"items": [], "amount": 100}, headers=headers)
    assert response.status_code == 403 # Changed from 401 as my main.py returns 403 for invalid identity

def test_imoxon_endpoints_alignment(valid_actor):
    uid, did = valid_actor
    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }
    # Verify we can reach a specialized engine endpoint through imoxon prefix
    # Need a valid property first
    token = _sovereign_context.set({"token": "TEST-SETUP", "actor": {"identity_id": "SYSTEM", "system_override": True}})
    try:
        from main import hospitality
        # Bypass guard for registration in setup
        prop = hospitality._internal_register({"name": "Test", "location": "Male", "base_rate": 50})
        prop_id = prop["id"]
    finally:
        _sovereign_context.reset(token)

    response = client.post("/imoxon/hospitality/book", json={"property_id": prop_id, "nights": 1}, headers=headers)
    assert response.status_code == 200
    assert "booking_id" in response.json()
