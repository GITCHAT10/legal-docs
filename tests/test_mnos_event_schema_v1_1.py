import pytest
import uuid
from datetime import datetime, UTC
from mnos.core.events.validator import validate_event

def create_valid_event():
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "CORE.SYSTEM.BOOT",
        "timestamp": datetime.now(UTC).isoformat(),
        "source": { "system": "CORE" },
        "actor": { "id": "sys_admin", "role": "ADMIN" },
        "context": {
            "tenant": { "brand": "MNOS", "tin": "123456", "jurisdiction": "MV" }
        },
        "payload": { "status": "UP" },
        "proof": {},
        "metadata": { "schema_version": "1.1" }
    }

def test_valid_event():
    event = create_valid_event()
    valid, msg = validate_event(event)
    assert valid, msg

def test_invalid_event_type():
    event = create_valid_event()
    event["event_type"] = "invalid.type"
    valid, msg = validate_event(event)
    assert not valid
    assert "Schema validation failed" in msg

def test_missing_field():
    event = create_valid_event()
    del event["payload"]
    valid, msg = validate_event(event)
    assert not valid
    assert "is a required property" in msg

def test_invalid_source():
    event = create_valid_event()
    event["source"]["system"] = "UNKNOWN_SYSTEM"
    valid, msg = validate_event(event)
    assert not valid
    assert "is not one of" in msg

def test_wrong_schema_version():
    event = create_valid_event()
    event["metadata"]["schema_version"] = "1.0"
    valid, msg = validate_event(event)
    assert not valid

def test_namespace_mismatch():
    event = create_valid_event()
    event["source"]["system"] = "QRD_MIG_SHIELD"
    event["event_type"] = "NOT_QRD.ACTION.START"
    valid, msg = validate_event(event)
    assert not valid
    assert "Namespace mismatch" in msg

def test_conditional_fce_proof():
    event = create_valid_event()
    event["event_type"] = "FCE.SETTLEMENT.COMPLETE"
    valid, msg = validate_event(event)
    assert not valid
    assert "Missing fce_settlement_ref" in msg

    event["proof"]["fce_settlement_ref"] = "SET-123"
    valid, msg = validate_event(event)
    assert valid
