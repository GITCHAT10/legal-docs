import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, mars_unified, transport, guard

client = TestClient(app)

@pytest.fixture
def agent_headers(create_hardened_identity):
    return create_hardened_identity("Agent", "agent")["headers"]

def test_maafushi_guest_order_flow(admin_headers, guest_headers):
    # 1. Setup: Register Owner and Vendor (Cafe Reef)
    owner_resp = client.post("/imoxon/itravel/owner/register", json={"legal_name": "Ahmed Maafushi"}, headers=admin_headers)
    owner_id = owner_resp.json()["id"]

    vendor_resp = client.post("/imoxon/itravel/vendor/register", json={
        "owner_id": owner_id, "name": "Cafe Reef", "island": "Maafushi", "vendor_type": "CAFE"
    }, headers=admin_headers)
    vendor_id = vendor_resp.json()["id"]

    # 2. Build Package
    pkg_resp = client.post("/imoxon/itravel/packages/build", json={
        "name": "Maafushi Lunch", "island": "Maafushi", "base_price": 100.0
    }, headers=admin_headers)
    pkg_id = pkg_resp.json()["id"]

    # 3. Process Cycle
    resp = client.post(f"/imoxon/itravel/cycle/process?guest_id=G1&package_id={pkg_id}", headers=admin_headers)
    assert resp.status_code == 200
    order = resp.json()
    assert order["status"] == "INITIATED"
    assert "transfer_id" in order

def test_accommodation_flow_with_green_tax(admin_headers, guest_headers):
    # 1. Setup Guesthouse
    owner_resp = client.post("/imoxon/itravel/owner/register", json={"legal_name": "Maafushi Owner"}, headers=admin_headers)
    owner_id = owner_resp.json()["id"]

    # 2. Build Package (Accommodation)
    pkg_resp = client.post("/imoxon/itravel/packages/build", json={
        "name": "Standard Room", "island": "Maafushi", "base_price": 500.0
    }, headers=admin_headers)
    pkg_id = pkg_resp.json()["id"]

    # 3. Process Cycle
    resp = client.post(f"/imoxon/itravel/cycle/process?guest_id=G2&package_id={pkg_id}", headers=admin_headers)
    assert resp.status_code == 200
    order = resp.json()
    # 500 + 10% SC = 550. 17% TGST of 550 = 93.5. Total = 643.5
    assert order["pricing"]["total"] == 643.5

def test_grid_control_stats(admin_headers):
    # Ensure stats run
    resp = client.get("/imoxon/grid-control/dashboard", headers=admin_headers)
    assert resp.status_code == 200
