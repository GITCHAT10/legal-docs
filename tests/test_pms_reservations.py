import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from main import app, pms_availability, guard, identity_core

client = TestClient(app)

@pytest.fixture
def auth_headers():
    # Setup SYSTEM identity for initialization
    with guard.sovereign_context({"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}):
        uid = identity_core.create_profile({"full_name": "PMS Admin", "profile_type": "admin"})
        did = identity_core.bind_device(uid, {"fingerprint": "pms-console-01"})
        identity_core.verify_identity(uid, "system")

    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-ISLAND-ID": "GLOBAL"
    }

def test_idempotency_replay(auth_headers):
    # Initialize inventory: 5 rooms
    pms_availability.initialize_inventory("RT1", 5, date(2026, 5, 10))

    payload = {
        "guest_id": "guest-001",
        "room_type_id": "RT1",
        "rate_plan_id": "RP1",
        "check_in": "2026-05-10",
        "check_out": "2026-05-13",
        "idempotency_key": "req_unique_001",
        "total_amount": 1250.00
    }

    # First call
    response1 = client.post("/pms/reservations", json=payload, headers=auth_headers)
    assert response1.status_code == 200
    res1 = response1.json()

    # Second call (replay)
    response2 = client.post("/pms/reservations", json=payload, headers=auth_headers)
    assert response2.status_code == 200
    res2 = response2.json()

    assert res1["id"] == res2["id"]
    # Verify only 1 room allocated in cache
    assert pms_availability.get_availability("RT1", date(2026, 5, 10), date(2026, 5, 13)) == 4

def test_double_booking_prevention(auth_headers):
    # Only 1 room available
    pms_availability.initialize_inventory("RT2", 1, date(2026, 5, 10))

    payload1 = {
        "guest_id": "guest-A",
        "room_type_id": "RT2",
        "rate_plan_id": "RP1",
        "check_in": "2026-05-10",
        "check_out": "2026-05-11",
        "idempotency_key": "req_A",
        "total_amount": 350.00
    }

    payload2 = payload1.copy()
    payload2["guest_id"] = "guest-B"
    payload2["idempotency_key"] = "req_B"

    # A books the last room
    res1 = client.post("/pms/reservations", json=payload1, headers=auth_headers)
    assert res1.status_code == 200

    # B tries to book the same room
    res2 = client.post("/pms/reservations", json=payload2, headers=auth_headers)
    # The guard re-raises ValueError as RuntimeError, and main.py returns 500 for RuntimeError
    # but the message contains our CONFLICT marker.
    assert res2.status_code == 500
    assert "CONFLICT" in res2.json()["detail"]

def test_shadow_audit_on_confirmation(auth_headers):
    from main import shadow_core
    initial_len = len(shadow_core.chain)

    pms_availability.initialize_inventory("RT3", 10, date(2026, 5, 15))

    payload = {
        "guest_id": "guest-C",
        "room_type_id": "RT3",
        "rate_plan_id": "RP1",
        "check_in": "2026-05-15",
        "check_out": "2026-05-16",
        "idempotency_key": "req_audit",
        "total_amount": 400.00
    }

    client.post("/pms/reservations", json=payload, headers=auth_headers)

    events = [b["event_type"] for b in shadow_core.chain[initial_len:]]
    assert "pms.reservation.create.intent" in events
    assert "pms.reservation.create.completed" in events

def test_cancel_releases_inventory(auth_headers):
    pms_availability.initialize_inventory("RT4", 1, date(2026, 5, 20))

    payload = {
        "guest_id": "guest-D",
        "room_type_id": "RT4",
        "rate_plan_id": "RP1",
        "check_in": "2026-05-20",
        "check_out": "2026-05-21",
        "idempotency_key": "req_cancel",
        "total_amount": 300.00
    }

    # Book
    res = client.post("/pms/reservations", json=payload, headers=auth_headers).json()
    res_id = res["id"]
    assert pms_availability.get_availability("RT4", date(2026, 5, 20), date(2026, 5, 21)) == 0

    # Cancel
    client.post(f"/pms/reservations/{res_id}/cancel", headers=auth_headers)

    # Verify availability restored
    assert pms_availability.get_availability("RT4", date(2026, 5, 20), date(2026, 5, 21)) == 1
