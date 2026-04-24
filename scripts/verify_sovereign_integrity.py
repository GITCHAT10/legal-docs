import sys
import os
from decimal import Decimal

# Ensure PYTHONPATH
sys.path.append(os.getcwd())

from mnos.modules.fce.service import fce
from mnos.modules.shadow.service import shadow
from mnos.core.security.aegis import aegis, SecurityException
from mnos.shared.execution_guard import guard, in_sovereign_context

def aegis_sign(payload):
    return aegis.sign_session(payload)

def verify_all():
    print("--- 🛡️ MNOS SOVEREIGN CORE: RC3 SECURITY INTEGRITY CHECK ---")

    # Reset state for clean verification
    shadow.chain = []
    shadow._seed_ledger()

    # 1. AEGIS Enforcement (P0)
    print("[1/3] Verifying AEGIS Enforcement...")
    # Signed session with trusted device should pass
    ctx = {
        "user_id": "U001",
        "session_id": "S001",
        "device_id": "nexus-001",
        "issued_at": "2026-04-24T12:00:00Z",
        "nonce": "N001"
    }
    ctx["signature"] = aegis_sign(ctx)
    assert aegis.validate_session(ctx) is True
    # Client-provided roles should be stripped. bound_device_id should be REJECTED.
    payload_with_roles = ctx.copy()
    payload_with_roles["roles"] = ["ADMIN"]
    ctx_with_roles = payload_with_roles.copy()
    ctx_with_roles["signature"] = aegis_sign(payload_with_roles)
    aegis.validate_session(ctx_with_roles)
    assert "roles" not in ctx_with_roles
    assert ctx_with_roles["verified_device_id"] == "nexus-001"
    print(" -> AEGIS Verified: OK")

    # 2. SHADOW Full-Chain Validation (P0)
    print("[2/3] Verifying SHADOW Full-Chain Integrity...")
    assert shadow.verify_integrity() is True

    # Seed some data
    t = in_sovereign_context.set(True)
    try:
        shadow.commit("test_event", {"data": "secure"})
    finally:
        in_sovereign_context.reset(t)
    assert shadow.verify_integrity() is True

    # Tamper test
    original_hash = shadow.chain[0]["hash"]
    shadow.chain[0]["hash"] = "CORRUPTED"
    assert shadow.verify_integrity() is False
    shadow.chain[0]["hash"] = original_hash
    print(" -> SHADOW Verified: OK")

    # 3. FCE Transaction Integrity
    print("[3/3] Verifying FCE Transaction Integrity...")
    # SC + TGST logic
    res = fce.calculate_folio(Decimal("100.00"))
    # 100 + 10% SC = 110. 110 * 17% TGST = 18.7. 110 + 18.7 + 6 GT = 134.7
    assert res["total"] == Decimal("134.70")
    print(" -> FCE Verified: OK")

    print("\n--- ✅ RC3 SECURITY INTEGRITY: PASSED ---")

if __name__ == "__main__":
    try:
        verify_all()
    except AssertionError as e:
        print(f"\n!!! SECURITY INTEGRITY FAILURE !!!")
        sys.exit(1)
    except Exception as e:
        print(f"\n!!! SYSTEM ERROR DURING VERIFICATION: {e} !!!")
        sys.exit(1)
