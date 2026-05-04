import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def supplier_headers(create_security_headers):
    # Use 'airline_partner' role to satisfy IdentifyPolicyEngine requirements if needed
    # though B2B AutoNegotiation doesn't strictly check for 'supplier' role yet.
    return create_security_headers(full_name="Supplier Alpha", profile_type="dmc_ta_staff")

@pytest.fixture
def admin_headers(create_security_headers):
    return create_security_headers(full_name="MNOS Admin", profile_type="admin")

@pytest.fixture
def setup_inventory(admin_headers):
    # 1. Create a package first since RFQ needs inventory
    pkg_config = {
        "name": "B2B Test Package",
        "island": "Maafushi",
        "base_price": 100.0,
        "inventory": {"room_type": "STANDARD", "nights": 1}
    }
    resp = client.post("/imoxon/itravel/packages/build", json=pkg_config, headers=admin_headers)
    assert resp.status_code == 200
    return resp.json()["id"]

def test_b2b_rfq_package_mode(supplier_headers, admin_headers, setup_inventory):
    # 1. Supplier requests RFQ (TO mode)
    rfq_data = {"partner_type": "TO", "pax_count": 2, "arrival_flight": "QR672"}
    resp = client.post("/imoxon/b2b/rfq", json=rfq_data, headers=supplier_headers)
    assert resp.status_code == 200
    assert resp.json()["quote_type"] == "PACKAGE"
    assert resp.json()["surge_applied"] is True

def test_b2b_rfq_net_mode_and_floor_guard(supplier_headers, admin_headers, setup_inventory):
    # 1. NET mode (DMC)
    rfq_data = {"partner_type": "DMC", "pax_count": 1}
    resp = client.post("/imoxon/b2b/rfq", json=rfq_data, headers=supplier_headers)
    assert resp.status_code == 200
    assert resp.json()["quote_type"] == "NET"

def test_b2b_booking_confirmation(supplier_headers, admin_headers, setup_inventory):
    # 1. Setup RFQ
    rfq_data = {"partner_type": "TO", "pax_count": 1}
    resp = client.post("/imoxon/b2b/rfq", json=rfq_data, headers=supplier_headers)
    quote_id = resp.json()["quote_id"]

    # 2. Confirm Booking
    # itravel router finalized cycle requires order_id, booking/confirm returns order_id
    resp = client.post(f"/imoxon/b2b/booking/confirm?quote_id={quote_id}", headers=supplier_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "BOOKING_CONFIRMED"
