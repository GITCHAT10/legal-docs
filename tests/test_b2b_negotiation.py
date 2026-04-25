import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, mars_unified

client = TestClient(app)

@pytest.fixture
def b2b_agent_headers():
    uid = identity_core.create_profile({
        "full_name": "Travel Agent X",
        "profile_type": "b2b_agent",
        "organization_id": "GLOBAL-TO"
    })
    did = identity_core.bind_device(uid, {"fingerprint": "agent-pc"})
    # Mocking B2B Realm for this session
    from main import identity_gateway
    session_id = f"SES-B2B-{uid[:4]}"
    identity_gateway.sessions[session_id] = {
        "identity_id": uid, "role": "b2b_agent", "realm": "B2B", "org_id": "GLOBAL-TO"
    }
    return {"X-AEGIS-SESSION": session_id}

@pytest.fixture
def admin_headers():
    uid = identity_core.create_profile({"full_name": "Root", "profile_type": "admin"})
    did = identity_core.bind_device(uid, {"fingerprint": "root-hw"})
    identity_core.verify_identity(uid, "SYS")
    return {"X-AEGIS-IDENTITY": uid, "X-AEGIS-DEVICE": did, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"}

def test_b2b_rfq_package_mode(admin_headers, b2b_agent_headers):
    # 1. Setup: Admin creates inventory
    client.post("/imoxon/itravel/packages/build", json={
        "name": "Luxury Maafushi", "island": "Maafushi", "base_price": 100.0
    }, headers=admin_headers)

    # 2. Agent RFQ in PACKAGE MODE (Tour Operator style)
    rfq_data = {"partner_type": "TO", "pax_count": 2, "arrival_flight": "QR672"}
    resp = client.post("/imoxon/b2b/rfq", json=rfq_data, headers=b2b_agent_headers)
    assert resp.status_code == 200
    quote = resp.json()
    assert quote["quote_type"] == "PACKAGE"
    assert quote["surge_applied"] is True # Due to QR672 flight

    # 100 (base) + 50 (transfer) + 30 (mege) + 20 (surge) = 200
    # 200 + 20 SC (10%) = 220
    # 220 + 37.4 TGST (17%) = 257.4
    # Total for 2 pax = 514.8
    assert quote["total_price"] == 514.8

def test_b2b_rfq_net_mode_and_floor_guard(admin_headers, b2b_agent_headers):
    # 1. Setup Low price inventory (below floor $40)
    client.post("/imoxon/itravel/packages/build", json={
        "name": "Budget Stay", "island": "Male", "base_price": 30.0
    }, headers=admin_headers)

    # 2. Agent RFQ in NET MODE (DMC style) - Should be rejected by floor guard
    rfq_data = {"partner_type": "DMC", "pax_count": 1}
    resp = client.post("/imoxon/b2b/rfq", json=rfq_data, headers=b2b_agent_headers)
    assert resp.status_code == 400
    assert "Rate below hotel floor" in resp.json()["detail"]

def test_b2b_booking_confirmation(admin_headers, b2b_agent_headers):
    # 1. Setup inventory
    client.post("/imoxon/itravel/packages/build", json={
        "name": "Standard Hotel", "island": "Hulhumale", "base_price": 60.0
    }, headers=admin_headers)

    # 2. Get Quote
    rfq_data = {"partner_type": "DMC", "pax_count": 1}
    resp = client.post("/imoxon/b2b/rfq", json=rfq_data, headers=b2b_agent_headers)
    quote_id = resp.json()["quote_id"]

    # 3. Confirm Booking
    resp = client.post(f"/imoxon/b2b/confirm?quote_id={quote_id}", headers=b2b_agent_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "BOOKING_CONFIRMED"
    assert "order_id" in resp.json()
