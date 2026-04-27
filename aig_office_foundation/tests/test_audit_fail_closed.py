import pytest
from ..shadow_audit.ledger import ShadowLedger
from ..shadow_audit.hash_chain import HashChain

def test_shadow_ledger_integrity():
    ledger = ShadowLedger()
    actor_id = "user-1"
    device_id = "dev-1"

    # Commit 1
    h1 = ledger.commit("test.event", actor_id, device_id, "trace-1", {"data": 1})
    # Commit 2
    h2 = ledger.commit("test.event", actor_id, device_id, "trace-2", {"data": 2})

    assert len(ledger.ledger) == 2
    assert ledger.verify_integrity() is True
    assert ledger.ledger[1]["prev_hash"] == h1

def test_shadow_ledger_tamper_detection():
    ledger = ShadowLedger()
    ledger.commit("test.event", "u1", "d1", "t1", {"data": 1})
    ledger.commit("test.event", "u1", "d1", "t2", {"data": 2})

    # Tamper with data
    ledger.ledger[0]["data"]["payload"]["data"] = 99

    assert ledger.verify_integrity() is False

def test_shadow_mandatory_trace_id():
    ledger = ShadowLedger()
    with pytest.raises(ValueError, match="trace_id is MANDATORY"):
        ledger.commit("test.event", "u1", "d1", "", {"data": 1})
