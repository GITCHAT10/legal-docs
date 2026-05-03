import pytest
from mnos.core.fce.settlement_events import emit_settlement_event
from mnos.core.events.validator import validate_event

def test_fce_settlement_event_validates():
    payload = {
        "settlement_id": "SET-123",
        "amount": 1000,
        "currency": "USD"
    }
    # For COMPLETE status, validator requires fce_settlement_ref
    event = emit_settlement_event("COMPLETE", payload)

    # Requirement: fce_settlement_ref should be in proof
    # Our implementation sets fce_settlement_ref to payload.get("settlement_id", "NONE")
    assert event["proof"]["fce_settlement_ref"] == "SET-123"

    valid, msg = validate_event(event)
    assert valid, msg

def test_fce_settlement_event_default_tenant():
    payload = {}
    event = emit_settlement_event("PENDING", payload)
    assert event["context"]["tenant"]["brand"] == "SALA"
    valid, msg = validate_event(event)
    assert valid, msg
