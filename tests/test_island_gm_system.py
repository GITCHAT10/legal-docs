import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def admin_headers():
    uid = identity_core.create_profile({
        "full_name": "Admin",
        "profile_type": "admin",
        "verification_status": "verified"
    })
    did = identity_core.bind_device(uid, {"fingerprint": "admin-hw"})
    identity_core.verify_identity(uid, "SYS")
    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

def test_island_gm_isolation_and_commission(admin_headers):
    # 1. Setup Maafushi GM
    gm_uid = identity_core.create_profile({
        "full_name": "Maafushi GM",
        "profile_type": "island_gm",
        "assigned_island": "Maafushi",
        "verification_status": "verified"
    })
    gm_did = identity_core.bind_device(gm_uid, {"fingerprint": "gm-tablet"})
    identity_core.verify_identity(gm_uid, "SYS")
    gm_headers = {
        "X-AEGIS-IDENTITY": gm_uid,
        "X-AEGIS-DEVICE": gm_did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{gm_uid}"
    }

    # 2. Register Island (Admin action)
    client.post("/imoxon/island-gm/registry/setup", json={"name": "Maafushi", "gm_id": gm_uid}, headers=admin_headers)
    client.post("/imoxon/island-gm/registry/setup", json={"name": "Thoddoo", "gm_id": "other"}, headers=admin_headers)

    # 3. Maafushi GM onboards local vendor to Maafushi (Allowed)
    resp = client.post("/imoxon/island-gm/vendors/onboard", json={
        "name": "Maafushi Cafe", "island": "Maafushi", "vendor_type": "CAFE", "owner_id": "some-owner"
    }, headers=gm_headers)
    assert resp.status_code == 200
    assert resp.json()["commission_rate"] > 0.05

    # 4. Maafushi GM tries to onboard to Thoddoo (Blocked)
    resp = client.post("/imoxon/island-gm/vendors/onboard", json={
        "name": "Thoddoo Shop", "island": "Thoddoo", "vendor_type": "RETAIL", "owner_id": "some-owner"
    }, headers=gm_headers)
    assert resp.status_code == 403

def test_island_dashboard_access(admin_headers):
    # Setup GM
    uid = identity_core.create_profile({
        "full_name": "G",
        "profile_type": "island_gm",
        "assigned_island": "Baa",
        "verification_status": "verified"
    })
    did = identity_core.bind_device(uid, {"fingerprint": "t1"})
    identity_core.verify_identity(uid, "SYS")
    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

    client.post("/imoxon/island-gm/registry/setup", json={"name": "Baa", "gm_id": uid}, headers=admin_headers)

    # GM can see their island
    resp = client.get("/imoxon/island-gm/dashboard?island=Baa", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["island"] == "Baa"

    # GM cannot see other island
    resp = client.get("/imoxon/island-gm/dashboard?island=Male", headers=headers)
    assert resp.status_code == 403
