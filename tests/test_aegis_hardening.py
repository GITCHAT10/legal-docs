import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def hardened_admin():
    identity_id = identity_core.create_profile({
        "full_name": "Hardened Admin",
        "profile_type": "admin"
    })
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "secure-device"})
    # Verify for hardened actions
    identity_core.verify_identity(identity_id, "SYSTEM-VERIFIER")

    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

def test_missing_signature_rejected(hardened_admin):
    headers = hardened_admin.copy()
    del headers["X-AEGIS-SIGNATURE"]
    resp = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert resp.status_code == 403
    assert "Missing Identity, Device or Signature" in resp.json()["detail"]

def test_invalid_signature_rejected(hardened_admin):
    headers = hardened_admin.copy()
    headers["X-AEGIS-SIGNATURE"] = "MALICIOUS_SIG"
    resp = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert resp.status_code == 403
    assert "Invalid Cryptographic Handshake" in resp.json()["detail"]

def test_unverified_identity_blocked_critical(hardened_admin):
    # Create unverified identity
    uid = identity_core.create_profile({"full_name": "Unverified", "profile_type": "admin"})
    did = identity_core.bind_device(uid, {"fingerprint": "d2"})
    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

    # Try a critical action: Register hospitality property
    resp = client.post("/imoxon/hospitality/properties/register", json={"name": "Fail Hotel"}, headers=headers)
    assert resp.status_code == 403
    assert "must be verified" in resp.json()["detail"]

def test_verified_identity_allowed_critical(hardened_admin):
    # Use the verified hardened_admin
    resp = client.post("/imoxon/hospitality/properties/register", json={"name": "Success Hotel", "base_rate": 100}, headers=hardened_admin)
    assert resp.status_code == 200
    assert "id" in resp.json()

def test_persistent_hash_returned_on_onboarding(hardened_admin):
    resp = client.post("/imoxon/suppliers/connect", params={"name": "Global Foods"}, headers=hardened_admin)
    assert resp.status_code == 200
    assert "persistent_hash" in resp.json()
