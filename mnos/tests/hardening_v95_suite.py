import pytest
import threading
from datetime import datetime, timezone
from mnos.core.security.aegis import aegis, SecurityException
from mnos.shared.execution_guard import guard, in_sovereign_context
from mnos.core.events.service import events
from mnos.modules.shadow.service import shadow

def get_valid_ctx():
    ctx = {
        "device_id": "nexus-admin-01",
        "nonce": "test-nonce-" + str(datetime.now().timestamp()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    ctx["signature"] = aegis.sign_session(ctx)
    return ctx

def test_unsigned_ctx_rejection():
    """Reject unsigned contexts."""
    ctx = {"device_id": "nexus-admin-01", "timestamp": datetime.now(timezone.utc).isoformat(), "nonce": "n1"}
    with pytest.raises(SecurityException) as excinfo:
        aegis.validate_session(ctx)
    assert "Missing required field: signature" in str(excinfo.value)

def test_forged_signature_rejection():
    """Reject forged signatures."""
    ctx = get_valid_ctx()
    ctx["signature"] = "forged"
    with pytest.raises(SecurityException) as excinfo:
        aegis.validate_session(ctx)
    assert "Session signature mismatch" in str(excinfo.value)

def test_device_mismatch_rejection():
    """Reject unauthorized devices."""
    ctx = {
        "device_id": "rogue-device",
        "nonce": "n2",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    ctx["signature"] = aegis.sign_session(ctx)
    with pytest.raises(SecurityException) as excinfo:
        aegis.validate_session(ctx)
    assert "Unauthorized device" in str(excinfo.value)

def test_timestamp_tamper_detection():
    """verify_integrity must fail if a block timestamp is tampered."""
    shadow.chain = shadow.chain[:1] # Reset to genesis
    guard.execute_sovereign_action("nexus.test", {"data": 1}, get_valid_ctx(), lambda p: "ok")

    # Tamper
    shadow.chain[1]["timestamp"] = "2020-01-01T00:00:00Z"
    assert shadow.verify_integrity() is False

def test_previous_hash_tamper_detection():
    """verify_integrity must fail if previous_hash is tampered."""
    shadow.chain = shadow.chain[:1]
    guard.execute_sovereign_action("nexus.test", {"data": 1}, get_valid_ctx(), lambda p: "ok")

    shadow.chain[1]["previous_hash"] = "0" * 64
    assert shadow.verify_integrity() is False

def test_direct_publish_rejection():
    """Reject all direct publish calls outside guard."""
    t = threading.current_thread()
    # Mock being outside guard
    orig_guard = getattr(t, 'in_sovereign_guard', False)
    orig_flag = getattr(t, 'sovereign_guard', False)
    t.in_sovereign_guard = False
    t.sovereign_guard = False

    try:
        with pytest.raises(RuntimeError) as excinfo:
            events.publish("nexus.test", {"data": "rogue"})
        assert "Direct publish bypass detected" in str(excinfo.value)
    finally:
        t.in_sovereign_guard = orig_guard
        t.sovereign_guard = orig_flag

def test_genesis_corruption_detection():
    """verify_integrity must fail if genesis block is corrupted."""
    shadow.chain = shadow.chain[:1]
    shadow.chain[0]["payload"] = {"tampered": True}
    assert shadow.verify_integrity() is False

if __name__ == "__main__":
    pytest.main([__file__])
