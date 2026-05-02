import pytest
from fastapi.testclient import TestClient
from main import app, shadow_core, guard, identity_core, pms_availability, booking_gate
from datetime import date
from mnos.shared.exceptions import ExecutionValidationError

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_state():
    from main import gateway, shield_edge
    gateway.rate_limits = {}
    shield_edge.rate_store = {}
    pms_availability.initialize_inventory("RT-AUTO", 10, date(2026, 6, 1), 30)
    booking_gate.booking_states = {}
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

def test_full_booking_gate_lifecycle(auth_headers):
    """E2E P0: DRAFT -> VALIDATED -> CONFIRMED -> EXECUTION_PENDING -> COMPLETED"""
    trace_id = "trace-lifecycle-789"

    # 1. Ingest (DRAFT -> VALIDATED)
    payload = {
        "booking_ref": "PRE-201",
        "room_type_id": "RT-AUTO",
        "check_in": "2026-06-01",
        "check_out": "2026-06-05",
        "total_amount": 3000.0,
        "trace_id": trace_id
    }
    resp1 = client.post("/imoxon/gate/ingest", json=payload, headers=auth_headers)
    assert resp1.status_code == 200
    booking_id = resp1.json()["id"]

    # 2. Confirm (VALIDATED -> CONFIRMED)
    pay_payload = {"payment_ref": "PAY-Lifecycle", "amount": 3000.0}
    resp2 = client.post(f"/imoxon/gate/{booking_id}/confirm", json=pay_payload, headers=auth_headers)
    assert resp2.status_code == 200

    # 3. Request Execution (CONFIRMED -> EXECUTION_PENDING)
    resp3 = client.post(f"/imoxon/gate/{booking_id}/execute", headers=auth_headers)
    assert resp3.status_code == 200

    # 4. Final Audit (Pre-Completion)
    resp4 = client.get(f"/imoxon/gate/{booking_id}/audit")
    # Score: 0.2 (init) + 0.2 (ingest) + 0.2 (payment) + 0.2 (exec_req) = 0.8
    assert resp4.json()["integrity_report"]["score"] == 0.8

    # 5. Complete Execution (EXECUTION_PENDING -> COMPLETED)
    signal = {"type": "GPS_GEOFENCE", "valid": True}
    resp5 = client.post(f"/imoxon/gate/{booking_id}/complete", json=signal, headers=auth_headers)
    assert resp5.status_code == 200
    assert resp5.json()["status"] == "COMPLETED"

    # 6. Final Audit (Post-Completion)
    resp6 = client.get(f"/imoxon/gate/{booking_id}/audit")
    assert resp6.json()["integrity_report"]["score"] == 1.0

def test_blocking_synthetic_execution(auth_headers):
    """Security: Cannot complete execution for unknown booking."""
    signal = {"type": "GPS_GEOFENCE", "valid": True}
    resp = client.post("/imoxon/gate/BK-UNKNOWN/complete", json=signal, headers=auth_headers)
    # ExecutionValidationError should result in 400 now via exception handler
    assert resp.status_code == 400
    assert "CANNOT_COMPLETE" in resp.json()["detail"]

def test_booking_gate_rejects_payment_mismatch(auth_headers):
    """Security: Payment amount must match quote."""
    payload = {
        "booking_ref": "PRE-102",
        "room_type_id": "RT-AUTO",
        "check_in": "2026-06-01",
        "check_out": "2026-06-05",
        "total_amount": 2000.0,
        "trace_id": "trace-fail-pay"
    }
    resp1 = client.post("/imoxon/gate/ingest", json=payload, headers=auth_headers)
    booking_id = resp1.json()["id"]

    # Attempt with wrong amount
    pay_payload = {"payment_ref": "PAY-ERR", "amount": 1000.0}
    resp2 = client.post(f"/imoxon/gate/{booking_id}/confirm", json=pay_payload, headers=auth_headers)
    assert resp2.status_code == 400
    assert "PAYMENT_MISMATCH" in resp2.json()["detail"]
