import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, mars_unified

client = TestClient(app)

@pytest.fixture
def admin_headers():
    identity_id = identity_core.create_profile({"full_name": "Admin", "profile_type": "admin"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "admin-dev"})
    identity_core.verify_identity(identity_id, "SYSTEM")
    return {
        "identity_id": identity_id,
        "device_id": device_id,
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

@pytest.fixture
def guest_headers():
    identity_id = identity_core.create_profile({"full_name": "Guest 102", "profile_type": "guest"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "guest-phone"})
    return {
        "identity_id": identity_id,
        "device_id": device_id,
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

def test_maafushi_guest_order_flow(admin_headers, guest_headers):
    # 1. Setup: Register Owner and Vendor (Cafe Reef)
    owner = mars_unified.register_owner(admin_headers, {"legal_name": "Ahmed Maafushi"})
    vendor = mars_unified.register_vendor(admin_headers, {
        "owner_id": owner["id"],
        "name": "Cafe Reef",
        "island": "Maafushi",
        "vendor_type": "CAFE"
    })
    vendor["id"]

    # 2. Build Package
    pkg = mars_unified.predict_and_build_package(admin_headers, {"name": "Maafushi Special", "island": "Maafushi", "base_price": 20.0})
    pkg_id = pkg["id"]

    # 3. Process Full Cycle
    resp = client.post(f"/imoxon/itravel/orders/full-cycle?guest_id={guest_headers['identity_id']}&package_id={pkg_id}", headers=admin_headers)
    assert resp.status_code == 200
    order = resp.json()
    order_id = order["id"]

    assert order["pricing"]["service_charge"] == 2.0
    assert order["pricing"]["tax_amount"] == 3.74
    assert order["pricing"]["total"] == 25.74

    # 4. Finalize
    resp = client.post(f"/imoxon/itravel/orders/finalize?order_id={order_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETED"

def test_grid_control_stats(admin_headers, guest_headers):
    resp = client.get("/imoxon/grid-control/dashboard", headers=admin_headers)
    assert resp.status_code == 200
    assert "total_orders" in resp.json()
