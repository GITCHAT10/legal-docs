import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def hardened_admin(create_security_headers):
    return create_security_headers(full_name="Hardened Admin", profile_type="admin")

def test_missing_signature_rejected(hardened_admin):
    headers = hardened_admin.copy()
    del headers["X-AEGIS-SIGNATURE"]
    resp = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert resp.status_code == 403
    assert "AEGIS_REQUIRED" in resp.json()["detail"]

def test_invalid_signature_rejected(hardened_admin):
    headers = hardened_admin.copy()
    headers["X-AEGIS-SIGNATURE"] = "MALICIOUS_SIG"
    resp = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert resp.status_code == 403
    assert "HANDSHAKE_FAILED" in resp.json()["detail"]

def test_unverified_identity_blocked_critical(create_security_headers):
    # Create unverified identity
    headers = create_security_headers(full_name="Unverified", profile_type="admin", verified=False)

    # Try a critical action: Register hospitality property
    resp = client.post("/imoxon/hospitality/properties/register", json={"name": "Fail Hotel"}, headers=headers)
    assert resp.status_code == 403
    assert "must be verified" in resp.json()["detail"]

def test_verified_identity_allowed_critical(hardened_admin):
    # Use the verified hardened_admin
    resp = client.post("/imoxon/hospitality/properties/register", json={"name": "Success Hotel", "base_rate": 100.0}, headers=hardened_admin)
    assert resp.status_code == 200
    assert "id" in resp.json()

def test_persistent_hash_returned_on_onboarding(hardened_admin):
    resp = client.post("/imoxon/suppliers/connect", params={"name": "Global Foods"}, headers=hardened_admin)
    assert resp.status_code == 200
    assert "persistent_hash" in resp.json()
