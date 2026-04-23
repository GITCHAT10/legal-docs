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
    ctx = {"device_id": "nexus-001"}
    ctx["signature"] = aegis_sign(ctx)
    assert aegis.validate_session(ctx) is True
    # Client-provided roles/binding should be stripped
    payload_to_sign = {"device_id": "nexus-001", "roles": ["ADMIN"], "bound_device_id": "SPOOF"}
    ctx_with_junk = payload_to_sign.copy()
    ctx_with_junk["signature"] = aegis_sign(payload_to_sign)
    aegis.validate_session(ctx_with_junk)
    assert "roles" not in ctx_with_junk
    assert "bound_device_id" not in ctx_with_junk
    assert ctx_with_junk["verified_device_id"] == "nexus-001"
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
