import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add mnos to path
sys.path.append(os.getcwd())

# Ensure NEXGEN_SECRET is set for tests
os.environ["NEXGEN_SECRET"] = "TEST-SECRET"

from main import app, identity_core

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_identity():
    # Setup some identities in the core
    admin_id = identity_core.create_profile({"full_name": "Admin User", "profile_type": "admin"})
    guest_id = identity_core.create_profile({"full_name": "Guest User", "profile_type": "guest"})

    # Verify Admin
    identity_core.verify_identity(admin_id, "SYSTEM")

    # Register devices for Guard requirements
    identity_core.bind_device(admin_id, {"fingerprint": "dev-01"})
    identity_core.bind_device(guest_id, {"fingerprint": "dev-02"})

    return {"admin": admin_id, "guest": guest_id}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_enterprise_dashboard(setup_identity):
    headers = {"X-AEGIS-IDENTITY": setup_identity["admin"], "X-AEGIS-DEVICE": "dev-01", "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + setup_identity["admin"]}
    response = client.get("/upos/enterprise/dashboard", headers=headers)
    assert response.status_code == 200
    assert response.json()["governance"] == "MAC EOS / MNOS"

def test_wifi_registration_admin(setup_identity):
    headers = {"X-AEGIS-IDENTITY": setup_identity["admin"], "X-AEGIS-DEVICE": "dev-01", "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + setup_identity["admin"]}
    payload = {"model": "WAVLINK HD6", "location": "Harbor Area"}
    response = client.post("/upos/u-wifi/register", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ONLINE"

def test_wifi_registration_guest_fail(setup_identity):
    headers = {"X-AEGIS-IDENTITY": setup_identity["guest"], "X-AEGIS-DEVICE": "dev-02", "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + setup_identity["guest"]}
    payload = {"model": "WAVLINK HD6", "location": "Harbor Area"}
    response = client.post("/upos/u-wifi/register", json=payload, headers=headers)
    # ORCA should block this
    assert response.status_code == 403
    assert "ORCA REJECTION" in response.json()["detail"]

def test_wifi_access_premium(setup_identity):
    headers = {"X-AEGIS-IDENTITY": setup_identity["guest"], "X-AEGIS-DEVICE": "dev-02", "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + setup_identity["guest"]}
    payload = {"guest_id": setup_identity["guest"], "package": "premium_speed", "room_id": "101"}
    response = client.post("/upos/u-wifi/access", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["bandwidth"] == "50Mbps"

def test_hotel_booking(setup_identity):
    # First register a property as admin
    admin_headers = {
        "identity_id": setup_identity["admin"],
        "device_id": "dev-01",
        "role": "admin",
        "verified": True
    }

    headers = {"X-AEGIS-IDENTITY": setup_identity["guest"], "X-AEGIS-DEVICE": "dev-02", "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + setup_identity["guest"]}
    # Mocking property registration in the engine directly for test
    from main import u_hotel
    prop = u_hotel.register_property(admin_headers, {"name": "SALA Resort", "base_rate": 500})

    payload = {"property_id": prop["id"], "nights": 2}
    response = client.post("/upos/u-hotel/book", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"

def test_apollo_sync(setup_identity):
    headers = {"X-AEGIS-IDENTITY": setup_identity["admin"], "X-AEGIS-DEVICE": "dev-01", "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_" + setup_identity["admin"]}
    events = [{"action_type": "wifi.access.issue", "actor_ctx": {"identity_id": setup_identity["guest"]}, "data": {}}]
    response = client.post("/upos/apollo/sync", json=events, params={"tenant_id": "T1"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["synced_count"] == 1
