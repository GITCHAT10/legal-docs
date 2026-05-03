import pytest
from mnos.core.shadow.ledger import ShadowLedger
from mnos.core.shadow.audit import record_audit_event
from datetime import datetime

def test_shadow_audit_timestamp_auto_population():
    ledger = ShadowLedger()
    record_audit_event(ledger, "AUDIT.TEST", "admin", {"data": "test"})

    # Check the block
    block = ledger.chain[0]
    assert block["timestamp"] is not None

    # Verify it's ISO formatted
    try:
        datetime.fromisoformat(block["timestamp"])
    except ValueError:
        pytest.fail("Timestamp is not ISO formatted")

def test_shadow_audit_record_no_null_timestamp():
    ledger = ShadowLedger()
    record_audit_event(ledger, "AUDIT.TEST", "admin", {"data": "test"})

    block = ledger.chain[0]
    # The event inside the block should also have the timestamp (as per ShadowLedger.commit implementation)
    assert block["event"].get("timestamp") is not None
    assert block["event"]["timestamp"] == block["timestamp"]
