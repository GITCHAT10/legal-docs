import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def admin_headers(create_security_headers):
    return create_security_headers(full_name="Admin", profile_type="admin")

@pytest.fixture
def guest_headers(create_security_headers):
    return create_security_headers(full_name="Guest", profile_type="user")

def test_nexus_skyi_closed_loop_economy(admin_headers, guest_headers):
    # 1. Setup Island
    client.post("/imoxon/island-gm/registry/setup", json={"name": "Maafushi", "gm_id": "GM-X"}, headers=admin_headers)

    # 2. TRAWEL Builds Package
    pkg_config = {
        "name": "Maafushi Weekend Explorer",
        "island": "Maafushi",
        "base_price": 500.0,
        "inventory": {"room_type": "DELUXE", "nights": 2}
    }
    resp = client.post("/imoxon/itravel/packages/build", json=pkg_config, headers=admin_headers)
    assert resp.status_code == 200
    pkg_id = resp.json()["id"]

    # 3. Guest Triggers Full Cycle
    guest_id = guest_headers["X-AEGIS-IDENTITY"]
    resp = client.post(f"/imoxon/itravel/orders/full-cycle?guest_id={guest_id}&package_id={pkg_id}", headers=guest_headers)
    assert resp.status_code == 200
    order_id = resp.json()["id"]

    # 4. Finalize
    resp = client.post(f"/imoxon/itravel/orders/finalize?order_id={order_id}", headers=admin_headers)
    assert resp.status_code == 200

def test_grid_control_admin_only(admin_headers, guest_headers):
    # Admin access
    resp = client.get("/imoxon/grid-control/dashboard", headers=admin_headers)
    assert resp.status_code == 200

    # Guest access
    resp = client.get("/imoxon/grid-control/dashboard", headers=guest_headers)
    assert resp.status_code == 403
