import pytest
import threading
from mnos.shared.execution_guard import guard, in_sovereign_context
from mnos.modules.shadow.service import shadow
from mnos.core.security.aegis import aegis

def test_shadow_commit_bypass_blocked():
    """Verify that direct shadow.commit() without guard context is blocked."""
    # Ensure guard context is NOT set
    token = in_sovereign_context.set(False)
    t = threading.current_thread()
    t.sovereign_guard = False

    try:
        with pytest.raises(RuntimeError) as excinfo:
            shadow.commit("BYPASS_EVENT", {"data": "rogue"})
        assert "SOVEREIGN VIOLATION" in str(excinfo.value)
        assert "Bypass detected" in str(excinfo.value)
    finally:
        in_sovereign_context.reset(token)

def test_shadow_monotonic_timestamp_enforced():
    """Verify that backdated commits are rejected."""
    session = {"device_id": "nexus-admin-01"}
    session["signature"] = aegis.sign_session(session)

    # 1. First valid commit
    guard.execute_sovereign_action(
        "nexus.test",
        {"v": 1},
        session,
        lambda p: "done"
    )

    # 2. Tamper with the chain to make the next real commit appear backdated
    # (Simulated by setting system clock back or manually injecting a future block)
    # But here we test the service logic:
    last_ts = shadow.chain[-1]["timestamp"]

    # We can't easily "backdate" a real commit since it uses datetime.now()
    # But we can verify verify_integrity fails if we manually backdate
    shadow.chain.append({
        "entry_id": len(shadow.chain),
        "timestamp": "2000-01-01T00:00:00Z", # way in the past
        "event_type": "BACKDATED",
        "payload": {},
        "previous_hash": shadow.chain[-1]["hash"]
    })
    # We need a hash for it too
    shadow.chain[-1]["hash"] = shadow._calculate_hash(shadow.chain[-1])

    assert shadow.verify_integrity() is False
    print("✔ Monotonicity enforced")

def test_unsigned_ctx_rejected():
    """Verify that ExecutionGuard rejects unsigned contexts."""
    session = {"device_id": "nexus-001"} # Missing signature

    with pytest.raises(RuntimeError) as excinfo:
        guard.execute_sovereign_action(
            "any.action",
            {},
            session,
            lambda p: "should fail"
        )
    assert "AEGIS_SIGNATURE_REQUIRED" in str(excinfo.value)

if __name__ == "__main__":
    pytest.main([__file__])
