import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def admin_ctx(admin_headers):
    # Ensure verified for hospitality actions
    aid = admin_headers["X-AEGIS-IDENTITY"]
    identity_core.verify_identity(aid, "TEST")
    return {
        "identity_id": aid,
        "device_id": admin_headers["X-AEGIS-DEVICE"],
        "role": "admin",
        "verified": True,
        "national_id_verified": True
    }

@pytest.fixture
def setup_hospitality(admin_headers):
    # Register a property via API
    prop_data = {"name": "Tune Maldives", "location": "Hulhumale", "base_rate": 50.0}
    resp = client.post("/imoxon/hospitality/properties/register", json=prop_data, headers=admin_headers)
    assert resp.status_code == 200
    return resp.json()["id"]

def test_airline_partner_discount(setup_hospitality):
    prop_id = setup_hospitality
    # Create airline partner actor
    uid = identity_core.create_profile({"full_name": "Airline Staff", "profile_type": "airline_partner"})
    did = identity_core.bind_device(uid, {"fingerprint": "phone-1"})
    identity_core.verify_identity(uid, "TEST")
    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

    booking_data = {"property_id": prop_id, "nights": 2, "amenities": ["aircon"]}
    resp = client.post("/imoxon/hospitality/book", json=booking_data, headers=headers)
    assert resp.status_code == 200
    booking = resp.json()

    assert booking["discount_applied"] == 25.0
    assert booking["pricing"]["base"] == 1310.70

def test_medical_worker_discount(setup_hospitality):
    prop_id = setup_hospitality
    uid = identity_core.create_profile({"full_name": "Doctor", "profile_type": "medical_worker"})
    did = identity_core.bind_device(uid, {"fingerprint": "phone-2"})
    identity_core.verify_identity(uid, "TEST")
    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

    booking_data = {"property_id": prop_id, "nights": 1}
    resp = client.post("/imoxon/hospitality/book", json=booking_data, headers=headers)
    assert resp.status_code == 200
    booking = resp.json()

    assert booking["discount_applied"] == 10.0
    assert booking["pricing"]["base"] == 616.80

def test_regular_user_no_discount(setup_hospitality):
    prop_id = setup_hospitality
    uid = identity_core.create_profile({"full_name": "Tourist", "profile_type": "tourist"})
    did = identity_core.bind_device(uid, {"fingerprint": "phone-3"})
    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

    booking_data = {"property_id": prop_id, "nights": 1}
    resp = client.post("/imoxon/hospitality/book", json=booking_data, headers=headers)
    assert resp.status_code == 200
    booking = resp.json()

    assert booking["discount_applied"] == 0.0
    assert booking["pricing"]["base"] == 771.0

def test_maldives_taxes_applied(setup_hospitality):
    prop_id = setup_hospitality
    uid = identity_core.create_profile({"full_name": "Tourist T", "profile_type": "tourist"})
    did = identity_core.bind_device(uid, {"fingerprint": "phone-4"})
    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

    resp = client.post("/imoxon/hospitality/book", json={"property_id": prop_id, "nights": 1}, headers=headers)
    assert resp.status_code == 200
    booking = resp.json()

    # Base MVR: 771.0
    # Service Charge: 10% = 77.10
    # Subtotal: 848.10
    # TGST (Tourism): 17% of 848.10 = 144.18
    # Green Tax (Guesthouse): $6 * 15.42 = 92.52
    # Total: 848.10 + 144.18 + 92.52 = 1084.8
    assert booking["pricing"]["service_charge"] == 77.10
    assert booking["pricing"]["tax_amount"] == 144.18
    assert booking["pricing"]["total"] == 1084.8
