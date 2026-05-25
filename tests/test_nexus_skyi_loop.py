import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, mars_unified, guard

client = TestClient(app)

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

    # 2. NEXUS Triggers Cycle
    resp = client.post(f"/imoxon/itravel/orders/full-cycle?guest_id=G-101&package_id={pkg_id}", headers=admin_headers)
    assert resp.status_code == 200
    order = resp.json()
    assert order["status"] == "INITIATED"
    assert order["pricing"]["total"] == 643.5 # 500 + 10% SC + 17% TGST on (550)

    # 3. Finalize and release payout
    resp = client.post(f"/imoxon/itravel/orders/finalize?order_id={order['id']}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETED"

def test_grid_control_admin_only(admin_headers, guest_headers):
    # Admin access
    resp = client.get("/imoxon/grid-control/dashboard", headers=admin_headers)
    assert resp.status_code == 200

    # Guest access denied
    resp = client.get("/imoxon/grid-control/dashboard", headers=guest_headers)
    assert resp.status_code == 403
