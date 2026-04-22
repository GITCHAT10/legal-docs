import pytest
from decimal import Decimal
from mnos.modules.fce.service import fce, FinancialException
from mnos.modules.shadow.service import shadow
from mnos.shared.execution_guard import guard
from mnos.core.security.aegis import aegis, SecurityException

def aegis_sign(payload):
    return aegis.sign_session(payload)

def test_identity_spoof_attack():
    """Simulate session payload tampering."""
    payload = {"device_id": "nexus-001", "user": "admin"}
    sig = aegis_sign(payload)

    # Attack: Change device_id but keep signature
    bad_payload = {"device_id": "nexus-attacker", "user": "admin", "signature": sig}

    with pytest.raises(SecurityException, match="signature mismatch"):
        guard.execute_sovereign_action("test", {}, bad_payload, lambda x: "fail")

def test_ledger_tampering_fail_closed():
    """Simulate head block tampering before next commit."""
    shadow.chain = []
    shadow._seed_ledger()

    ctx = {"device_id": "nexus-001"}
    ctx["signature"] = aegis_sign(ctx)

    # 1. Valid commit
    guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "ok")

    # 2. Tamper
    shadow.chain[1]["payload"]["result"] = "TAMPERED"

    # 3. Next attempt should fail CLOSED
    with pytest.raises(RuntimeError, match="Chain corruption detected"):
        guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "ok")

def test_partial_transaction_failure_recovery():
    """Verify system remains atomic even if execution logic fails."""
    shadow.chain = []
    shadow._seed_ledger()
    initial_len = len(shadow.chain)

    ctx = {"device_id": "nexus-001"}
    ctx["signature"] = aegis_sign(ctx)

    def logic_fails(p):
        raise ValueError("EXECUTION CRASHED")

    with pytest.raises(ValueError, match="EXECUTION CRASHED"):
        guard.execute_sovereign_action("event.fail", {}, ctx, logic_fails)

    # Audit trail should NOT have commit for failed execution (Execution Guard Order)
    assert len(shadow.chain) == initial_len
    assert shadow.verify_integrity() is True
