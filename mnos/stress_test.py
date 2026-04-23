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

    # Needs guard context for publish
    from mnos.shared.execution_guard import in_sovereign_context
    t = in_sovereign_context.set(True)
    try:
        events.publish("nexus.booking.created", {"data": "test"})
    finally:
        in_sovereign_context.reset(t)

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
    ctx = {"device_id": "nexus-001"}
    from mnos.core.security.aegis import aegis
    ctx["signature"] = aegis.sign_session(ctx)

    whatsapp.receive_message("+9602", "book room", ctx)
    whatsapp.receive_message("+9603", "arrival at airport", ctx)
    whatsapp.receive_message("+9604", "emergency help", ctx)
    print(f"Final Ledger Size: {len(shadow.chain)}")
    print(f"Final Integrity: {shadow.verify_integrity()}")

    print("\n--- ✅ STRESS TESTS COMPLETE ---")

if __name__ == "__main__":
    stress_test()
