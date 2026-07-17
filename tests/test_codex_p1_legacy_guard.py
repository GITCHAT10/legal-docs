import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, shadow_core

client = TestClient(app)

@pytest.fixture
def unverified_user():
    uid = identity_core.create_profile({"full_name": "Unverified", "profile_type": "user"})
    did = identity_core.bind_device(uid, {"fingerprint": "dev-u1"})
    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

@pytest.fixture
def verified_user():
    uid = identity_core.create_profile({"full_name": "Verified", "profile_type": "user"})
    did = identity_core.bind_device(uid, {"fingerprint": "dev-v1"})
    identity_core.verify_identity(uid, "SYSTEM")
    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

def test_legacy_order_creation_guarded_and_audited(verified_user):
    """
    P1 REGRESSION: legacy create_order is guarded/audited.
    verified authorized actor succeeds.
    """
    initial_len = len(shadow_core.chain)

    resp = client.post("/imoxon/itravel/orders/create", params={"vendor_id": "v1", "amount": 100.0}, headers=verified_user)
    assert resp.status_code == 200
    order = resp.json()
    assert "order_id" in order

    # Verify SHADOW intent/completed audit is produced (2 events)
    assert len(shadow_core.chain) >= initial_len + 2

    intent_event = shadow_core.chain[-2]
    assert intent_event["event_type"] == "itravel.legacy_order.create.intent"
    assert intent_event["actor_id"] == verified_user["X-AEGIS-IDENTITY"]

    completed_event = shadow_core.chain[-1]
    assert completed_event["event_type"] == "itravel.legacy_order.create.completed"

def test_legacy_order_creation_blocked_for_unverified(unverified_user):
    """
    P1 REGRESSION: unverified authenticated actor calling legacy order create gets 403.
    """
    # itravel.legacy_order.create doesn't explicitly require verification in IdentityPolicyEngine
    # but the instructions say "verified authorized actor succeeds" and "unverified ... gets 403".
    # I need to ensure it's in the hardened_actions or similar in IdentityPolicyEngine.

    resp = client.post("/imoxon/itravel/orders/create", params={"vendor_id": "v1", "amount": 100.0}, headers=unverified_user)
    # If PolicyEngine doesn't block it, this will be 200. I need to update PolicyEngine.
    assert resp.status_code == 403
