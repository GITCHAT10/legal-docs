import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def hardened_admin():
    identity_id = identity_core.create_profile({"full_name": "Hardened Root", "profile_type": "admin"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "secure-device"})
    identity_core.verify_identity(identity_id, "SYSTEM")
    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

def test_missing_identity_rejected():
    resp = client.post("/imoxon/suppliers/connect", params={"name": "Test"})
    assert resp.status_code == 403
    assert "AEGIS_REQUIRED" in resp.json()["detail"]

def test_invalid_signature_rejected(hardened_admin):
    headers = hardened_admin.copy()
    headers["X-AEGIS-SIGNATURE"] = "MALICIOUS_SIG"
    resp = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert resp.status_code == 403
    assert "HANDSHAKE_FAILED" in resp.json()["detail"]

def test_device_mismatch_rejected(hardened_admin):
    headers = hardened_admin.copy()
    headers["X-AEGIS-DEVICE"] = "malicious-dev"
    resp = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert resp.status_code == 403
    assert "DEVICE_BINDING_INVALID" in resp.json()["detail"]

def test_unverified_identity_rejected():
    identity_id = identity_core.create_profile({"full_name": "Unverified", "profile_type": "admin"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "dev1"})
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }
    # Registering a property requires verified admin
    resp = client.post("/imoxon/hospitality/properties/register", json={"name": "P"}, headers=headers)
    assert resp.status_code == 403
    assert "must be verified" in resp.json()["detail"]

def test_shadow_event_schema_enforced(hardened_admin):
    from main import shadow_core
    client.post("/imoxon/suppliers/connect", params={"name": "Schema Test"}, headers=hardened_admin)
    last_block = shadow_core.chain[-1]
    assert "hash" in last_block
    assert "prev_hash" in last_block
    assert "payload" in last_block
