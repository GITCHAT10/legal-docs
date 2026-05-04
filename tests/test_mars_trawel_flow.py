import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def admin_headers(create_security_headers):
    return create_security_headers(full_name="Admin", profile_type="admin")

@pytest.fixture
def guest_headers(create_security_headers):
    return create_security_headers(full_name="Tourist", profile_type="user")

def test_maafushi_guest_order_flow(admin_headers, guest_headers):
    # 1. Register the island first
    client.post("/imoxon/island-gm/registry/setup", json={"name": "Male", "gm_id": "GM-MALE"}, headers=admin_headers)

    # 2. Build Package
    pkg_config = {"name": "Male Weekend", "island": "Male", "base_price": 400.0, "inventory": {"room": "SUPERIOR"}}
    resp = client.post("/imoxon/itravel/packages/build", json=pkg_config, headers=admin_headers)
    pkg_id = resp.json()["id"]

    # 3. Guest Triggers Full Cycle
    guest_id = guest_headers["X-AEGIS-IDENTITY"]
    resp = client.post(f"/imoxon/itravel/orders/full-cycle?guest_id={guest_id}&package_id={pkg_id}", headers=guest_headers)
    assert resp.status_code == 200
    order_id = resp.json()["id"]

    # 4. Finalize Order
    resp = client.post(f"/imoxon/itravel/orders/finalize?order_id={order_id}", headers=admin_headers)
    # If it fails 400, it's because of missing SYSTEM_DEFAULT_VENDOR in vendors for reinvestment signal
    # Let's check it
    if resp.status_code != 200:
        print(f"DEBUG: {resp.text}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETED"

def test_accommodation_flow_with_green_tax(admin_headers, guest_headers):
    pkg_config = {"name": "Ukulhas Stay", "island": "Ukulhas", "base_price": 100.0}
    resp = client.post("/imoxon/itravel/packages/build", json=pkg_config, headers=admin_headers)
    pkg_id = resp.json()["id"]

    guest_id = guest_headers["X-AEGIS-IDENTITY"]
    resp = client.post(f"/imoxon/itravel/orders/full-cycle?guest_id={guest_id}&package_id={pkg_id}", headers=guest_headers)
    assert resp.status_code == 200

    assert resp.json()["pricing"]["total"] == 128.7

def test_grid_control_stats(admin_headers, guest_headers):
    # 1. Access dashboard
    resp = client.get("/imoxon/grid-control/dashboard", headers=admin_headers)
    assert resp.status_code == 200
    assert "total_orders" in resp.json()

    # 2. Unauthorized access
    resp = client.get("/imoxon/grid-control/dashboard", headers=guest_headers)
    assert resp.status_code == 403
