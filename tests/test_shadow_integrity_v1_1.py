import pytest
from mnos.core.shadow.ledger import ShadowLedger
from mnos.core.shadow.integrity import verify_chain_integrity

def test_shadow_integrity():
    ledger = ShadowLedger()
    event1 = {"event_type": "CORE.START", "payload": {"status": "ok"}}
    event2 = {"event_type": "CORE.STOP", "payload": {"status": "off"}}

    ledger.commit(event1)
    ledger.commit(event2)

    assert verify_chain_integrity(ledger)

def test_shadow_tampering():
    ledger = ShadowLedger()
    event = {"event_type": "FCE.SETTLE", "payload": {"amount": 1000}}
    ledger.commit(event)

    assert verify_chain_integrity(ledger)

    # Tamper with payload
    ledger.chain[0]["event"]["payload"]["amount"] = 9999
    assert not verify_chain_integrity(ledger)

def test_shadow_timestamp_tampering():
    ledger = ShadowLedger()
    event = {"event_type": "FCE.SETTLE", "payload": {"amount": 1000}}
    ledger.commit(event)

    assert verify_chain_integrity(ledger)

    # Tamper with timestamp
    ledger.chain[0]["timestamp"] = "2000-01-01T00:00:00Z"
    assert not verify_chain_integrity(ledger)
