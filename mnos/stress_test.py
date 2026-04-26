from mnos.shared.guard.test_signer import aegis_sign
import sys
import os
import uuid
from decimal import Decimal

# Add path
sys.path.append(os.getcwd())

from mnos.modules.fce.service import fce, FinancialException
from mnos.modules.shadow.service import shadow
from mnos.core.events.service import events
from mnos.core.asi.silvia import silvia
from mnos.interfaces.sky_i.comms.whatsapp import whatsapp
from mnos.modules.knowledge.service import knowledge_core

# Import workflows
import mnos.modules.workflows.booking
import mnos.modules.workflows.guest_arrival
import mnos.modules.workflows.emergency

def stress_test():
    print("--- 🛡️ NEXUS ASI SKY-i HARDENING STRESS TESTS ---")

    # 0. Initialize DNA for tests
    knowledge_core.ingest("TEST_DNA", "Bookings and Arrivals and Emergencies are active.")

    # 1. Fail-closed authority test (FCE)
    print("\n[TEST 1: Fail-closed FCE]")
    try:
        fce.validate_pre_auth("F-ERR", Decimal("10000"), Decimal("100"))
        print("FAILED: Pre-auth should have failed.")
    except FinancialException as e:
        print(f"SUCCESS: System blocked high-risk transaction: {e}")

    # 2. Corruption Recovery Test
    print("\n[TEST 2: Corruption Recovery]")
    # Clear chain for clean test
    shadow.chain = shadow.chain[:1]

    # Needs guard
    from mnos.shared.execution_guard import guard
    from mnos.core.security.aegis import aegis
    import time
    ctx_stress = {
        "user_id": "STRESS-INIT",
        "session_id": "STRESS",
        "device_id": "nexus-001",
        "issued_at": int(time.time()),
        "nonce": "N-STRESS-INIT"
    }
    ctx_stress["signature"] = aegis_sign(ctx_stress)
    guard.execute_sovereign_action("nexus.booking.created", {"data": "test"}, ctx_stress, lambda x: None)

    original_integrity = shadow.verify_integrity()
    print(f"Original Integrity: {original_integrity}")

    # Tamper
    shadow.chain[1]["payload"] = {"TAMPERED": "TRUE"}
    tampered_integrity = shadow.verify_integrity()
    print(f"Tampered Integrity: {tampered_integrity}")
    if not tampered_integrity:
        print("SUCCESS: Integrity alarm triggered on corruption.")

    # Restore
    shadow.chain = shadow.chain[:1]

    # 3. Threshold Adversarial Test
    print("\n[TEST 3: Threshold Adversarial]")
    res = silvia.process_request("What is the weather?")
    print(f"SILVIA status for unknown: {res['status']} (Should be ESCALATE)")

    # 4. Concurrency Test (Simulated Sequential but overlapping logic)
    print("\n[TEST 4: Concurrency Simulation]")
    # Use trusted hardware ID from Registry
    import time
    ctx = {
        "user_id": "STRESS-01",
        "session_id": "S-STRESS-01",
        "device_id": "nexus-001",
        "issued_at": int(time.time()),
        "nonce": "N-STRESS-01"
    }
    from mnos.core.security.aegis import aegis
    ctx["signature"] = aegis_sign(ctx)

    whatsapp.receive_message("+9602", "book room", ctx.copy())

    # 3rd and 4th calls need fresh signatures and context snapshots
    ctx_base = {
        "user_id": "STRESS-01",
        "session_id": "S-STRESS-01",
        "device_id": "nexus-001",
        "issued_at": int(time.time())
    }

    ctx3 = ctx_base.copy()
    ctx3["nonce"] = "N-STRESS-02"
    ctx3["signature"] = aegis_sign(ctx3)
    whatsapp.receive_message("+9603", "arrival at airport", ctx3)

    ctx4 = ctx_base.copy()
    ctx4["nonce"] = "N-STRESS-03"
    ctx4["signature"] = aegis_sign(ctx4)
    whatsapp.receive_message("+9604", "emergency help", ctx4)
    print(f"Final Ledger Size: {len(shadow.chain)}")
    print(f"Final Integrity: {shadow.verify_integrity()}")

    print("\n--- ✅ STRESS TESTS COMPLETE ---")

if __name__ == "__main__":
    stress_test()
