import pytest
from fastapi.testclient import TestClient
from main import app, shadow_core, guard, identity_core, pms_availability
from datetime import date, timedelta

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_system_state():
    from main import gateway, shield_edge
    gateway.rate_limits = {}
    shield_edge.rate_store = {}

    # Initialize inventory for tests
    start = date(2026, 6, 1)
    pms_availability.initialize_inventory("RT-PREMIUM", 10, start, 30)
    pms_availability.initialize_inventory("RT-STD", 10, start, 30)

    yield

@pytest.fixture
def auth_headers():
    with guard.sovereign_context({"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}):
        uid = identity_core.create_profile({"full_name": "Booking Agent", "profile_type": "staff"})
        did = identity_core.bind_device(uid, {"fingerprint": "agent-dev-01"})
        identity_core.verify_identity(uid, "system")

    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-ISLAND-ID": "GLOBAL"
    }

def test_reservation_with_privacy_premium(auth_headers):
    """Monetization: Booking a Shielded Villa must apply premium pricing and SHADOW anchor."""
    booking_payload = {
        "guest_id": "GUEST-PRIVACY-001",
        "room_type_id": "RT-PREMIUM",
        "villa_id": "SV-101", # Shielded Villa
        "rate_plan_id": "RP-DAILY",
        "check_in": "2026-06-01",
        "check_out": "2026-06-05",
        "idempotency_key": "res-privacy-101",
        "total_amount": 1000.0 # Base amount
    }

    response = client.post("/pms/reservations", json=booking_payload, headers=auth_headers)
    assert response.status_code == 200
    res_data = response.json()

    # 1. Verify Premium Pricing (Multiplier is 1.2 for SV-101)
    assert res_data["base_amount"] == 1000.0
    assert res_data["total_amount"] == 1200.0
    assert res_data["privacy_multiplier"] == 1.2
    assert res_data["privacy_premium_active"] is True

    # 2. Verify Legal Clause
    assert "Shielded Villa Privacy Assurance Addendum" in res_data["metadata"]["privacy_legal_clause"]

    # 3. Verify SHADOW Audit
    events = [b["event_type"] for b in shadow_core.chain]
    assert "pms.reservation.create.completed" in events

    res_block = next(b for b in shadow_core.chain if b["event_type"] == "pms.reservation.create.completed")
    assert res_block["payload"]["result"]["total_amount"] == 1200.0
    assert res_block["payload"]["result"]["privacy_premium_active"] is True

def test_standard_reservation_no_premium(auth_headers):
    """Monetization: Standard villa booking has no multiplier."""
    booking_payload = {
        "guest_id": "GUEST-STD-002",
        "room_type_id": "RT-STD",
        "villa_id": "ST-201", # Standard Villa
        "rate_plan_id": "RP-DAILY",
        "check_in": "2026-06-10",
        "check_out": "2026-06-12",
        "idempotency_key": "res-std-201",
        "total_amount": 500.0
    }

    response = client.post("/pms/reservations", json=booking_payload, headers=auth_headers)
    assert response.status_code == 200
    res_data = response.json()

    assert res_data["total_amount"] == 500.0
    assert res_data["privacy_multiplier"] == 1.0
    assert res_data["privacy_premium_active"] is False
    assert "Airspace Awareness & Privacy Assurance Clause" in res_data["metadata"]["privacy_legal_clause"]
