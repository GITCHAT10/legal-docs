import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def setup_identity():
    # Setup a valid identity and device in the core
    identity_id = identity_core.create_profile({
        "full_name": "Authorized Admin",
        "profile_type": "admin",
        "organization_id": "MIG-HQ"
    })
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "secure-fingerprint"})
    return identity_id, device_id

def test_missing_headers_rejected():
    response = client.post("/imoxon/suppliers/connect", params={"name": "Test"})
    assert response.status_code == 403
    assert "Missing Identity or Device" in response.json()["detail"]

def test_fake_identity_rejected(setup_identity):
    identity_id, device_id = setup_identity
    headers = {
        "X-AEGIS-IDENTITY": "fake-id",
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_fake-id"
    }
    response = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert response.status_code == 403
    assert "INVALID_IDENTITY" in response.json()["detail"]

def test_unbound_device_rejected(setup_identity):
    identity_id, device_id = setup_identity
    other_id = identity_core.create_profile({"full_name": "Other", "profile_type": "user"})

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
    response = client.post("/imoxon/suppliers/connect", params={"name": "Authorized Supplier"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Authorized Supplier"
