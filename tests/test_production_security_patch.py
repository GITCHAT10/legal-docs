import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def setup_identity():
    # Setup a valid identity and device in the core
    identity_id = identity_core.create_profile({
        "full_name": "Patch Admin",
        "profile_type": "admin",
        "organization_id": "MIG-HQ"
    })
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "secure-fingerprint"})
    return identity_id, device_id

def test_unauthorized_header_injection_fails():
    # Attempting to fake a role via headers
    headers = {
        "X-AEGIS-IDENTITY": "fake-id",
        "X-AEGIS-DEVICE": "fake-device",
        "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_fake-id"
    }
    response = client.post("/imoxon/orders/create", json={"items": [], "amount": 100}, headers=headers)
    assert response.status_code == 403

def test_imoxon_endpoints_alignment(setup_identity):
    identity_id, device_id = setup_identity
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

    # 1. Supplier connect
    resp = client.post("/imoxon/suppliers/connect", json={"name": "Test Supplier"}, headers=headers)
    assert resp.status_code == 200
    sid = resp.json()["id"]

    # 2. Product Import
    prod_data = [{"name": "Global Item", "price": 100.0}]
    resp = client.post(f"/imoxon/products/import?sid={sid}", json=prod_data, headers=headers)
    assert resp.status_code == 200
