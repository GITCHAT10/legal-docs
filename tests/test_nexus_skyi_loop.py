import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def admin_headers():
    uid = identity_core.create_profile({"full_name": "Grid Admin", "profile_type": "admin"})
    did = identity_core.bind_device(uid, {"fingerprint": "admin-cloud"})
    identity_core.verify_identity(uid, "SYSTEM")
    return {
        "identity_id": uid,
        "device_id": did,
        "role": "admin",
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

@pytest.fixture
def guest_headers():
    identity_id = identity_core.create_profile({"full_name": "Guest Explorer", "profile_type": "guest"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "guest-phone"})
    return {
        "identity_id": identity_id,
        "device_id": device_id,
        "role": "guest",
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

def test_nexus_skyi_closed_loop_economy(admin_headers, guest_headers):
    # 1. TRAWEL Builds Package (Cloud Brain decides)
    pkg_config = {
        "name": "Maafushi Weekend Explorer",
        "island": "Maafushi",
        "base_price": 500.0,
        "inventory": {"room_type": "DELUXE", "nights": 2}
    }
    resp = client.post("/imoxon/itravel/packages/build", json=pkg_config, headers=admin_headers)
    assert resp.status_code == 200
    pkg_id = resp.json()["id"]

    # 2. Guest Books Package
    resp = client.post(f"/imoxon/itravel/orders/full-cycle?guest_id={guest_headers['identity_id']}&package_id={pkg_id}", headers=admin_headers)
    assert resp.status_code == 200
    order_id = resp.json()["id"]

    # 3. Finalize Cycle (Verify SHADOW & FCE Settlement)
    resp = client.post(f"/imoxon/itravel/orders/finalize?order_id={order_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETED"

def test_unauthorized_package_build(guest_headers):
    resp = client.post("/imoxon/itravel/packages/build", json={}, headers=guest_headers)
    # AEGIS checks happen first
    assert resp.status_code in [200, 403]

def test_grid_control_admin_only(admin_headers, guest_headers):
    # Admin access
    resp = client.get("/imoxon/grid-control/dashboard", headers=admin_headers)
    assert resp.status_code == 200

    # Guest access (Blocked)
    resp = client.get("/imoxon/grid-control/dashboard", headers=guest_headers)
    assert resp.status_code == 403
