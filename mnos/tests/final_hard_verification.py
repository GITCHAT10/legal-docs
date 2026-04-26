from mnos.shared.guard.test_signer import aegis_sign
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
import hmac
import hashlib
from mnos.core.apollo.registry import apollo_registry

@pytest.fixture(autouse=True)
def reset_system():
    shadow.chain = []
    shadow._seed_ledger()
    # Reset Registry State
    apollo_registry._system_locked = False
    apollo_registry._used_nonces = set()
    aegis.registry.reset_state()

def test_unauthorized_user_rejection():
    """P0: Prove that a user not in the registry is rejected regardless of payload."""
    ctx = {
        "user_id": "ATTACKER",
        "session_id": "S-ROGUE",
        "device_id": "nexus-001",
        "issued_at": int(time.time()),
        "nonce": "N-ROGUE"
    }
    # No signature will match because user isn't in node map
    ctx["signature"] = "any_hash"

    with pytest.raises(SecurityException, match="failed cryptographic verification"):
        guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "fail")

def test_revoked_unknown_device_rejection():
    """P0: Prove unknown hardware IDs are blocked."""
    ctx = {
        "user_id": "GUEST-01",
        "session_id": "S-01",
        "device_id": "unknown-device-123",
        "issued_at": int(time.time()),
        "nonce": "N-01"
    }
    # Signature is for nexus-001 (authorized for GUEST-01) but device_id in payload is different
    ctx["signature"] = aegis_sign(ctx)

    # Now that we enforce device_id matching, this must fail
    with pytest.raises(SecurityException, match="failed cryptographic verification"):
        guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "success")

def test_device_id_mismatch_rejection():
    """P0: Regression - Reject if user claims a device they aren't authorized for."""
    # CEO-01 is authorized for nexus-admin-01
    ctx = {
        "user_id": "CEO-01",
        "session_id": "S-MISMATCH",
        "device_id": "nexus-001", # WRONG DEVICE
        "issued_at": int(time.time()),
        "nonce": "N-MISMATCH"
    }
    ctx["signature"] = aegis_sign(ctx)

    with pytest.raises(SecurityException, match="failed cryptographic verification"):
        guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "success")

def test_rate_limiting_enforcement():
    """P0: Verify rate limiting blocks excessive requests."""
    ctx = {
        "user_id": "CEO-01",
        "session_id": "S-RATE",
        "device_id": "nexus-admin-01",
        "issued_at": int(time.time()),
        "nonce": "N-RATE-"
    }

    # First 10 should pass (reset_system clears used nonces and registry state)
    for i in range(10):
        test_ctx = ctx.copy()
        test_ctx["nonce"] = f"N-RATE-{i}"
        test_ctx["signature"] = aegis_sign(test_ctx)
        guard.execute_sovereign_action("nexus.booking.created", {}, test_ctx, lambda x: "ok")

    # 11th should fail rate limit
    test_ctx = ctx.copy()
    test_ctx["nonce"] = "N-RATE-11"
    test_ctx["signature"] = aegis_sign(test_ctx)
    with pytest.raises(SecurityException, match="Rate limit exceeded"):
        guard.execute_sovereign_action("nexus.booking.created", {}, test_ctx, lambda x: "ok")

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

    res = guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "success")
    assert res == "success"

def test_shadow_genesis_tamper_rejection():
    """P1: Prove that modifying block 0 (Genesis) fails integrity."""
    assert shadow.verify_integrity() is True
    # Tamper with genesis payload
    shadow.chain[0]["payload"]["tamper"] = True
    assert shadow.verify_integrity() is False
    assert apollo_registry.is_locked() is True

def test_fail_closed_on_ledger_corruption():
    """P0: Prove workflow is blocked if ledger is already corrupt."""
    # Ensure system is locked
    apollo_registry.lock_system("Manual Lock for Test")

    ctx = {
        "user_id": "CEO-01",
        "session_id": "S-SEC",
        "device_id": "nexus-admin-01",
        "issued_at": int(time.time()),
        "nonce": "N-SEC"
    }
    # Sign it properly
    ctx["signature"] = aegis_sign(ctx)

    with pytest.raises(SecurityException, match="SYSTEM HALT"):
        guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "executed")

def test_replay_attack_blocked():
    """P0: Prove that re-using a nonce fails verification."""
    ctx = {
        "user_id": "CEO-01",
        "session_id": "S-REPLAY",
        "device_id": "nexus-admin-01",
        "issued_at": int(time.time()),
        "nonce": "NONCE-REPLAY-1"
    }
    ctx["signature"] = aegis_sign(ctx)

    # 1. First attempt OK
    guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "ok")

    # 2. Second attempt with same nonce FAIL
    with pytest.raises(SecurityException, match="failed cryptographic verification"):
        guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "ok")
