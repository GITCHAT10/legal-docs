import pytest
import time
import uuid
from decimal import Decimal
from mnos.core.security.aegis import aegis, SecurityException
from mnos.modules.shadow.service import shadow
from mnos.modules.fce.service import fce
from mnos.shared.execution_guard import guard, in_sovereign_context
from mnos.config import config
import mnos.modules.workflows.booking

def aegis_sign(payload):
    return aegis.sign_session(payload)

@pytest.fixture(autouse=True)
def reset_system():
    shadow.chain = []
    shadow._seed_ledger()
    # Reset AEGIS registry and session maps if needed
    # Note: HardwareRegistry is per-instance of AegisService

def test_forged_aegis_session_bypass_attempt():
    """P0: Prove that setting device_id == bound_device_id in payload is REJECTED."""
    ctx = {
        "user_id": "ATTACKER",
        "session_id": "S-ROGUE",
        "device_id": "nexus-001",
        "bound_device_id": "nexus-001", # Client attempt to inject trusted field
        "issued_at": int(time.time()),
        "nonce": "N-ROGUE"
    }
    ctx["signature"] = aegis_sign(ctx)

    with pytest.raises(SecurityException, match="Security Breach Attempt"):
        guard.execute_sovereign_action("test", {}, ctx, lambda x: "fail")

def test_revoked_unknown_device_rejection():
    """P0: Prove unknown hardware IDs are blocked."""
    ctx = {
        "user_id": "GUEST-01",
        "session_id": "S-01",
        "device_id": "unknown-device-123",
        "issued_at": int(time.time()),
        "nonce": "N-01"
    }
    ctx["signature"] = aegis_sign(ctx)

    with pytest.raises(SecurityException, match="is not authorized on"):
        guard.execute_sovereign_action("test", {}, ctx, lambda x: "fail")

def test_valid_signed_device_acceptance():
    """P0: Prove valid hardware and signed context are accepted."""
    ctx = {
        "user_id": "CEO-01",
        "session_id": "S-VALID",
        "device_id": "nexus-admin-01",
        "issued_at": int(time.time()),
        "nonce": "N-VALID"
    }
    ctx["signature"] = aegis_sign(ctx)

    # Use a real event type from TAXONOMY
    res = guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "success")
    assert res == "success"

def test_shadow_genesis_tamper_rejection():
    """P1: Prove that modifying block 0 (Genesis) fails integrity."""
    # 1. Verify healthy start
    assert shadow.verify_integrity() is True

    # 2. Tamper with genesis previous_hash (which should be "0"*64)
    shadow.chain[0]["previous_hash"] = "TAMPERED"
    assert shadow.verify_integrity() is False

def test_shadow_middle_chain_tamper_rejection():
    """P1: Prove that modifying a middle block breaks the hash chain."""
    ctx = {
        "user_id": "CEO-01", "session_id": "S-1", "device_id": "nexus-admin-01",
        "issued_at": int(time.time()), "nonce": "N-1"
    }
    ctx["signature"] = aegis_sign(ctx)
    guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "ok")

    ctx2 = {
        "user_id": "CEO-01", "session_id": "S-2", "device_id": "nexus-admin-01",
        "issued_at": int(time.time()), "nonce": "N-2"
    }
    ctx2["signature"] = aegis_sign(ctx2)
    guard.execute_sovereign_action("nexus.payment.received", {}, ctx2, lambda x: "ok")

    # Chain: [0] Genesis, [1] booking.created, [2] payment.received (via workflow), [3] payment.received (direct)
    assert len(shadow.chain) == 4

    # Tamper with event.1
    shadow.chain[1]["payload"]["action"] = "MODIFIED"
    assert shadow.verify_integrity() is False

def test_fail_closed_on_identity_failure():
    """P0: Prove workflow is blocked if identity validation fails."""
    ctx = {
        "user_id": "GUEST-01", "session_id": "S-FAIL", "device_id": "nexus-001",
        "issued_at": 0, # EXPIRED
        "nonce": "N-FAIL"
    }
    ctx["signature"] = aegis_sign(ctx)

    with pytest.raises(SecurityException, match="expired or stale"):
        guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "executed")

    # Ensure no event reached SHADOW
    assert len(shadow.chain) == 1 # Only Genesis

def test_fail_closed_on_ledger_corruption():
    """P0: Prove workflow is blocked if ledger is already corrupt."""
    # 1. Corrupt the ledger
    shadow.chain[0]["hash"] = "BURNT"

    ctx = {
        "user_id": "CEO-01", "session_id": "S-SEC", "device_id": "nexus-admin-01",
        "issued_at": int(time.time()), "nonce": "N-SEC"
    }
    ctx["signature"] = aegis_sign(ctx)

    with pytest.raises(RuntimeError, match="Chain corruption detected"):
        guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "executed")
