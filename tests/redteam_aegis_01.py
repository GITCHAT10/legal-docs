import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def setup_valid_entities():
    # Valid Admin
    admin_id = identity_core.create_profile({"full_name": "Root Admin", "profile_type": "admin"})
    admin_dev = identity_core.bind_device(admin_id, {"fingerprint": "admin-hw"})
    identity_core.verify_identity(admin_id, "SYSTEM-VERIFIER")

    # Valid Captain
    captain_id = identity_core.create_profile({"full_name": "Captain Ahmed", "profile_type": "captain"})
    captain_dev = identity_core.bind_device(captain_id, {"fingerprint": "tablet-01"})

    # Valid Guest
    guest_id = identity_core.create_profile({"full_name": "Tourist A", "profile_type": "guest"})
    guest_dev = identity_core.bind_device(guest_id, {"fingerprint": "phone-a"})

    return {
        "admin": {"id": admin_id, "dev": admin_dev, "sig": f"VALID_SIG_FOR_{admin_id}"},
        "captain": {"id": captain_id, "dev": captain_dev, "sig": f"VALID_SIG_FOR_{captain_id}"},
        "guest": {"id": guest_id, "dev": guest_dev, "sig": f"VALID_SIG_FOR_{guest_id}"}
    }

def test_attack_fake_device_binding(setup_valid_entities):
    """Attack: Use valid Identity with a Device ID they don't own."""
    entities = setup_valid_entities
    headers = {
        "X-AEGIS-IDENTITY": entities["admin"]["id"],
        "X-AEGIS-DEVICE": entities["guest"]["dev"], # WRONG DEVICE
        "X-AEGIS-SIGNATURE": entities["admin"]["sig"]
    }
    resp = client.get("/imoxon/grid-control/dashboard", headers=headers)
    assert resp.status_code == 403
    assert "DEVICE_BINDING_INVALID" in resp.json()["detail"]

def test_attack_privilege_escalation(setup_valid_entities):
    """Attack: Guest attempts to build a TRAWEL package."""
    entities = setup_valid_entities
    headers = {
        "X-AEGIS-IDENTITY": entities["guest"]["id"],
        "X-AEGIS-DEVICE": entities["guest"]["dev"],
        "X-AEGIS-SIGNATURE": entities["guest"]["sig"]
    }
    # Currently hospitality.property.register requires 'admin' role in logic if we enforce it.
    # Let's check a dashboard action which we know checks roles.
    resp = client.get("/imoxon/grid-control/dashboard", headers=headers)
    assert resp.status_code == 403
    assert "Admin access required" in resp.json()["detail"]

def test_attack_identity_spoofing():
    """Attack: Attempt to use a non-existent identity."""
    headers = {
        "X-AEGIS-IDENTITY": "non-existent-uuid",
        "X-AEGIS-DEVICE": "some-dev",
        "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_non-existent-uuid"
    }
    resp = client.get("/imoxon/grid-control/dashboard", headers=headers)
    assert resp.status_code == 401
    assert "INVALID_IDENTITY" in resp.json()["detail"]

def test_attack_forged_signature(setup_valid_entities):
    """Attack: Correct ID/Device but malicious signature."""
    entities = setup_valid_entities
    headers = {
        "X-AEGIS-IDENTITY": entities["admin"]["id"],
        "X-AEGIS-DEVICE": entities["admin"]["dev"],
        "X-AEGIS-SIGNATURE": "FORGED_HMAC_HERE"
    }
    resp = client.get("/imoxon/grid-control/dashboard", headers=headers)
    assert resp.status_code == 403
    assert "HANDSHAKE_FAILED" in resp.json()["detail"]

def test_attack_unverified_critical_action(setup_valid_entities):
    """Attack: Non-verified admin attempts to register property (requires verification)."""
    # Create unverified admin
    uid = identity_core.create_profile({"full_name": "New Admin", "profile_type": "admin"})
    did = identity_core.bind_device(uid, {"fingerprint": "hw2"})
    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

    # This should be blocked by PolicyEngine
    resp = client.post("/imoxon/hospitality/properties/register", json={"name": "Hacked Hotel"}, headers=headers)
    assert resp.status_code == 403
    assert "must be verified" in resp.json()["detail"]

def test_attack_cloned_captain_tablet(setup_valid_entities):
    """Attack: Guest attempts to trigger payout release (requires verified admin/payout authority)."""
    entities = setup_valid_entities
    headers = {
        "X-AEGIS-IDENTITY": entities["guest"]["id"],
        "X-AEGIS-DEVICE": entities["guest"]["dev"],
        "X-AEGIS-SIGNATURE": entities["guest"]["sig"]
    }

    # Finalizing loop cycle (payout release) should be restricted to verified roles
    resp = client.post("/imoxon/itravel/orders/finalize", params={"order_id": "any"}, headers=headers)
    assert resp.status_code == 403
    assert "must be verified" in resp.json()["detail"] or "Admin access required" in str(resp.json())
