import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, shadow_core, b2b_negotiator, mars_unified

client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture(autouse=True)
def clear_state():
    mars_unified.packages.clear()
    mars_unified.orders.clear()
    mars_unified.settlements.clear()
    b2b_negotiator.quotes.clear()
    identity_core.profiles.clear()
    identity_core.devices.clear()

def test_p1_reject_caller_supplied_identity_id():
    # Attempt to create identity with pre-set ID
    evil_id = "evil-admin-id"
    resp = client.post("/imoxon/aegis/identity/create", json={
        "full_name": "Evil Actor",
        "profile_type": "admin",
        "identity_id": evil_id
    })
    assert resp.status_code == 200
    returned_id = resp.json()["identity_id"]

    # Prove the evil_id was ignored
    assert returned_id != evil_id
    assert evil_id not in identity_core.profiles
    assert returned_id in identity_core.profiles

def test_p2_audit_permission_error_after_intent():
    # Setup B2B Agent
    uid = identity_core.create_profile({"full_name": "B2B Agent", "profile_type": "b2b_agent"})
    did = identity_core.bind_device(uid, {"fingerprint": "agent-hw"})
    identity_core.verify_identity(uid, "SYS")

    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

    # 1. Setup inventory with price below floor ($40)
    admin_uid = identity_core.create_profile({"full_name": "Admin", "profile_type": "admin"})
    admin_did = identity_core.bind_device(admin_uid, {"fingerprint": "admin-hw"})
    admin_headers = {
        "X-AEGIS-IDENTITY": admin_uid,
        "X-AEGIS-DEVICE": admin_did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{admin_uid}"
    }
    client.post("/imoxon/itravel/packages/build", json={
        "name": "Cheap Room", "island": "Male", "base_price": 30.0
    }, headers=admin_headers)

    # 2. Trigger RFQ which will fail Floor Guard (PermissionError in logic)
    initial_chain_len = len(shadow_core.chain)
    resp = client.post("/imoxon/b2b/rfq", json={"partner_type": "DMC", "pax_count": 1}, headers=headers)

    assert resp.status_code == 403
    assert "Rate below hotel floor" in resp.json()["detail"]

    # 3. Verify terminal audit entry exists
    # Intent + Committed (if success) OR Intent + Failed (if rollback)
    # We expect .intent AND .failed
    events = [b["event_type"] for b in shadow_core.chain[initial_chain_len:]]
    assert "b2b.rfq.intent" in events
    assert "b2b.rfq.failed" in events

    failure_block = [b for b in shadow_core.chain if b["event_type"] == "b2b.rfq.failed"][-1]
    assert failure_block["payload"]["status"] == "FAILED_ROLLBACK"
    assert "Rate below hotel floor" in failure_block["payload"]["error"]
