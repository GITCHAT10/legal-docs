import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, mars_unified

client = TestClient(app)

@pytest.fixture
def admin_headers():
    identity_id = identity_core.create_profile({"full_name": "Admin", "profile_type": "admin"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "admin-dev"})
    return {"X-AEGIS-IDENTITY": identity_id, "X-AEGIS-DEVICE": device_id}

@pytest.fixture
def guest_headers():
    identity_id = identity_core.create_profile({"full_name": "Guest 102", "profile_type": "guest"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "guest-phone"})
    return {"X-AEGIS-IDENTITY": identity_id, "X-AEGIS-DEVICE": device_id}

def test_maafushi_guest_order_flow(admin_headers, guest_headers):
    # 1. Setup: Register Owner and Vendor (Cafe Reef)
    owner = mars_unified.register_owner(admin_headers, {"legal_name": "Ahmed Maafushi"})
    vendor = mars_unified.register_vendor(admin_headers, {
        "owner_id": owner["id"],
        "name": "Cafe Reef",
        "island": "Maafushi",
        "vendor_type": "CAFE"
    })
    vendor_id = vendor["id"]

    # 2. Guest Orders worth $20
    # $20 Base -> $2 SC -> $3.74 TGST -> $25.74 Total
    resp = client.post(f"/imoxon/itravel/orders/create?vendor_id={vendor_id}&amount=20.0", headers=guest_headers)
    assert resp.status_code == 200
    order = resp.json()
    order_id = order["order_id"]

    assert order["pricing"]["service_charge"] == 2.0
    assert order["pricing"]["tax_amount"] == 3.74
    assert order["pricing"]["total"] == 25.74

    # 3. Verify MARS PAY Settlement Split
    # Base $20: MARS 4% ($0.80), NGO 2% ($0.40), Vendor Net $18.80
    settlement = mars_unified.settlements[order_id]
    assert settlement["mars_fee"] == 0.80
    assert settlement["ngo_fee"] == 0.40
    assert settlement["vendor_net"] == 18.80
    assert settlement["tax_vault"] == 5.74 # 2 SC + 3.74 TGST
    assert settlement["payout_status"] == "PENDING"

    # 4. Delivery Flow: FLOW-CAPTAIN Update
    resp = client.post(f"/imoxon/flow/delivery/update?order_id={order_id}&status=DELIVERED", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["delivery_status"] == "DELIVERED"

    # 5. Verify Payout Released
    assert mars_unified.settlements[order_id]["payout_status"] == "RELEASED"

def test_accommodation_flow_with_green_tax(admin_headers, guest_headers):
    # 1. Setup Guesthouse
    owner = mars_unified.register_owner(admin_headers, {"legal_name": "Maafushi Owner"})
    vendor = mars_unified.register_vendor(admin_headers, {
        "owner_id": owner["id"],
        "name": "Maafushi Guesthouse",
        "island": "Maafushi",
        "vendor_type": "GUESTHOUSE"
    })
    vendor_id = vendor["id"]

    # 2. Order Room for $100
    # $100 Base + $10 SC + $18.70 TGST + $6 Green Tax (converted to MVR)
    # Green Tax in MVR = 6 * 15.42 = 92.52
    resp = client.post(f"/imoxon/itravel/orders/create?vendor_id={vendor_id}&amount=100.0", headers=guest_headers)
    assert resp.status_code == 200
    order = resp.json()

    assert order["pricing"]["service_charge"] == 10.0
    assert order["pricing"]["tax_amount"] == 18.70
    assert order["pricing"]["green_tax"] == 92.52
    # 100 + 10 + 18.70 + 92.52 = 221.22
    assert order["pricing"]["total"] == 221.22

def test_grid_control_stats(admin_headers, guest_headers):
    # Ensure some orders exist
    mars_unified.get_grid_control_stats() # just check it runs
    resp = client.get("/imoxon/grid-control/dashboard", headers=admin_headers)
    assert resp.status_code == 200
    assert "total_orders" in resp.json()
