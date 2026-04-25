import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def setup_identity():
    # Valid identity in the database
    identity_id = identity_core.create_profile({
        "full_name": "Valid User",
        "profile_type": "user"
    })
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "secure-fingerprint"})
    return identity_id, device_id

def test_unauthorized_header_injection_fails():
    # Attempting to fake a role via headers (if it were possible)
    headers = {
        "X-AEGIS-IDENTITY": "fake-id",
        "X-AEGIS-DEVICE": "fake-device",
        "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_fake-id"
    }
    response = client.post("/imoxon/orders/create", json={"items": [], "amount": 100}, headers=headers)
    assert response.status_code == 401
    assert "INVALID_IDENTITY" in response.json()["detail"]

def test_valid_aegis_identity_passes(setup_identity):
    identity_id, device_id = setup_identity
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }
    response = client.post("/imoxon/orders/create", json={"items": [], "amount": 100}, headers=headers)
    # Success here depends on procurement engine logic for empty items,
    # but at least it should pass AEGIS auth.
    assert response.status_code in [200, 422]

def test_device_mismatch_blocks(setup_identity):
    identity_id, device_id = setup_identity
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": "wrong-device",
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }
    response = client.post("/imoxon/orders/create", json={"items": [], "amount": 100}, headers=headers)
    assert response.status_code == 403
    assert "DEVICE_BINDING_INVALID" in response.json()["detail"]

def test_imoxon_endpoints_alignment(setup_identity):
    identity_id, device_id = setup_identity
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

    # 1. Supplier connect
    resp = client.post("/imoxon/suppliers/connect", params={"name": "Test Supplier"}, headers=headers)
    assert resp.status_code == 200
    assert "supplier_id" in resp.json()
    assert "persistent_hash" in resp.json()

    # 2. Product import (using returned supplier_id)
    sid = resp.json()["supplier_id"]
    resp = client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Fish", "price": 10}, headers=headers)
    assert resp.status_code == 200
