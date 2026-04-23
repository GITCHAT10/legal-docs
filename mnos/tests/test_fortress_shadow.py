import pytest
import json
from mnos.modules.aig_shadow.service import aig_shadow

def test_shadow_deterministic_hashing():
    # Test that different key orders in payload produce same hash
    payload1 = {"a": 1, "b": 2}
    payload2 = {"b": 2, "a": 1}

    # We can't easily test commit without the whole guard chain,
    # so we test the _calculate_hash directly.
    entry1 = {
        "entry_id": 1,
        "event_type": "TEST",
        "payload": payload1,
        "previous_hash": "abc",
        "timestamp": "2026-01-01T00:00:00Z"
    }
    entry2 = entry1.copy()
    entry2["payload"] = payload2

    assert aig_shadow._calculate_hash(entry1) == aig_shadow._calculate_hash(entry2)

def test_shadow_integrity_verification():
    # Chain is already seeded with genesis
    assert aig_shadow.verify_integrity() is True

    # Tamper with genesis
    original_hash = aig_shadow.chain[0]["hash"]
    aig_shadow.chain[0]["hash"] = "tampered"
    assert aig_shadow.verify_integrity() is False

    # Restore
    aig_shadow.chain[0]["hash"] = original_hash
    assert aig_shadow.verify_integrity() is True
