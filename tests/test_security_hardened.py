import pytest
from fastapi.testclient import TestClient
from main import app, identity_core
from mnos.shared.execution_guard import _sovereign_context

client = TestClient(app)

@pytest.fixture
def setup_identity():
    # Setup a valid identity and device in the core
    # Requires sovereign context for direct write to shadow
    token = _sovereign_context.set({"token": "TEST-SETUP", "actor": {"identity_id": "SYSTEM"}})
    try:
        identity_id = identity_core.create_profile({
            "full_name": "Authorized Admin",
            "profile_type": "admin",
            "organization_id": "MIG-HQ"
        })
        device_id = identity_core.bind_device(identity_id, {"fingerprint": "secure-fingerprint"})
        # Verify it to pass critical action checks
        identity_core.verify_identity(identity_id, "SYSTEM")
        return identity_id, device_id
    finally:
        _sovereign_context.reset(token)

def test_missing_headers_rejected():
    response = client.post("/imoxon/suppliers/connect", params={"name": "Test"})
    assert response.status_code == 403
    assert "AEGIS_REQUIRED" in response.json()["detail"]

def test_fake_identity_rejected(setup_identity):
    identity_id, device_id = setup_identity
    headers = {
        "X-AEGIS-IDENTITY": "fake-id",
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_fake-id"
    }
    response = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert response.status_code == 403
    assert "INVALID_IDENTITY" in response.json()["detail"]

def test_unbound_device_rejected(setup_identity):
    identity_id, device_id = setup_identity

    # Create another identity
    token = _sovereign_context.set({"token": "TEST-SETUP", "actor": {"identity_id": "SYSTEM"}})
    try:
        other_id = identity_core.create_profile({"full_name": "Other", "profile_type": "user"})
    finally:
        _sovereign_context.reset(token)

    headers = {
        "X-AEGIS-IDENTITY": other_id,
        "X-AEGIS-DEVICE": device_id, # device bound to identity_id, not other_id
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{other_id}"
    }
    response = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert response.status_code == 403
    assert "DEVICE_BINDING_INVALID" in response.json()["detail"]

def test_authorized_access(setup_identity):
    identity_id, device_id = setup_identity
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }
    # Connect supplier tries to create a profile, which might fail if policy engine is strict.
    # But for now we just want to see why it fails with 403.
    response = client.post("/imoxon/suppliers/connect", params={"name": "Authorized Supplier"}, headers=headers)
    if response.status_code != 200:
        print(f"DEBUG: {response.json()}")
    assert response.status_code == 200
    assert response.json()["name"] == "Authorized Supplier"
    assert "supplier_id" in response.json()
