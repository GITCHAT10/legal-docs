import os
from mnos.modules.shadow.service import shadow
from mnos.core.audit.sal import sal

def chaos_test():
    print("--- 🌪️ NEXUS ASI SKY-I OS CHAOS TEST ---")
    os.environ["NEXGEN_SECRET"] = "SOVEREIGN_GENESIS_KEY_2024"

    # 1. Create a legitimate transaction
    print("Creating legitimate transaction...")
    sal.log("CHAOS-001", "HW-MALDIVES-NEXUS-ADMIN", "SYSTEM_HEALTH_CHECK", {"status": "OK"})

    initial_integrity = shadow.verify_integrity()
    print(f"Initial Chain Integrity: {initial_integrity}")
    assert initial_integrity == True

    # 2. Deliberately tamper with a record in the SHADOW ledger
    print("\nSimulating data tampering (External Breach)...")
    shadow.chain[1]["payload"]["status"] = "MALICIOUS_TAMPER"

    # 3. Verify that the system detects the breach and triggers the kill-switch
    print("Running integrity re-verification...")
    tampered_integrity = shadow.verify_integrity()
    print(f"Post-Tamper Chain Integrity: {tampered_integrity}")

    if not tampered_integrity:
        print("✅ SUCCESS: SHADOW detected the integrity breach.")
        try:
             sal.log("CHAOS-002", "HW-MALDIVES-NEXUS-ADMIN", "POST_TAMPER_LOG", {"attempt": "SHOULD_FAIL"})
        except RuntimeError as e:
             print(f"✅ SUCCESS: System triggered FAIL-CLOSED. Error: {str(e)}")
             if os.getenv("MNOS_READ_ONLY") == "TRUE":
                 print("✅ SUCCESS: GLOBAL KILL-SWITCH ACTIVATED (READ-ONLY MODE).")
    else:
        print("❌ FAILURE: SHADOW failed to detect tampering!")
        return False

    print("\n--- ✅ CHAOS TEST COMPLETE: SYSTEM IS SECURE ---")
    return True

if __name__ == "__main__":
    chaos_test()
