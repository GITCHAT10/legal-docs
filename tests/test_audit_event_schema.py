import pytest
from mnos.core.shadow.ledger import ShadowLedger
from mnos.core.shadow.audit import record_audit_event
from mnos.core.events.validator import validate_event

def test_audit_event_schema_compliance():
    ledger = ShadowLedger()
    record_audit_event(ledger, "CORE.AUDIT.TEST", "admin", {"data": "test"})

    event = ledger.chain[0]["event"]
    valid, msg = validate_event(event)
    assert valid, msg
