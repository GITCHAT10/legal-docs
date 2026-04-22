import sys
import os
import uuid
from decimal import Decimal

# Path setup
sys.path.append(os.getcwd())

from mnos.modules.fce.service import fce, FinancialException
from mnos.modules.shadow.service import shadow
from mnos.core.events.service import events
from mnos.core.ai.silvia import silvia
from mnos.interfaces.sky_i.comms.whatsapp import whatsapp
from mnos.modules.knowledge.service import knowledge_core

# Load workflows
import mnos.modules.workflows.booking
import mnos.modules.workflows.guest_arrival
import mnos.modules.workflows.emergency

def fail_closed_authority_test():
    print("[TEST] fail_closed_authority_test")
    try:
        fce.validate_pre_auth("FAIL-GATE", Decimal("1000000"), Decimal("100"))
        return False
    except FinancialException:
        print(" -> PASSED: FCE blocked unauthorized amount.")

    original_chain = shadow.chain
    shadow.chain = None
    try:
        shadow.commit("TEST", {})
        return False
    except RuntimeError:
        print(" -> PASSED: SHADOW halted system on commit failure.")
    finally:
        shadow.chain = original_chain
    return True

def idempotency_replay_test():
    print("[TEST] idempotency_replay_test")
    trace = str(uuid.uuid4())
    payload = {"data": "idempotency-test"}
    events.publish("nexus.booking.created", payload, trace_id=trace)
    len1 = len(shadow.chain)
    events.publish("nexus.booking.created", payload, trace_id=trace)
    len2 = len(shadow.chain)
    if len2 > len1:
        print(f" -> PASSED: Audit trail captured replay.")
        return True
    return False

def shadow_integrity_break_test():
    print("[TEST] shadow_integrity_break_test")
    # Reset and seed
    shadow.chain = []
    shadow._seed_ledger()
    events.publish("nexus.booking.created", {"data": "test"})

    # Tamper with the genesis block event_type
    shadow.chain[0]["event_type"] = "TAMPERED"

    # Now verify_integrity() should fail because block 0 hash no longer matches content,
    # OR block 1's previous_hash won't match block 0's recomputed hash.
    # Note: verify_integrity recomputes hash of current block and checks against its stored hash.

    integrity_ok = shadow.verify_integrity()
    if not integrity_ok:
        print(" -> PASSED: Integrity break detected.")
        return True
    else:
        print(" -> FAILED: Integrity break NOT detected.")
        # Debugging
        entry = shadow.chain[0]
        recomputed = shadow._calculate_hash(entry)
        print(f"Entry 0 Hash: {entry['hash']}")
        print(f"Recomputed:  {recomputed}")
        return False

def silvia_adversarial_threshold_test():
    print("[TEST] silvia_adversarial_threshold_test")
    res = silvia.process_request("I want to eat something")
    if res["status"] == "ESCALATE":
        print(f" -> PASSED: Silvia escalated low-intent request.")
        return True
    return False

def concurrent_workflow_collision_test():
    print("[TEST] concurrent_workflow_collision_test")
    shadow.chain = []
    shadow._seed_ledger()
    knowledge_core.ingest("FINAL_DNA", "Bookings and Arrivals and Emergencies active.")
    ctx = {"device_id": "nexus-1", "bound_device_id": "nexus-1"}
    whatsapp.receive_message("+9601", "Book room", ctx)
    whatsapp.receive_message("+9602", "Arrival", ctx)
    whatsapp.receive_message("+9603", "SOS Emergency", ctx)
    if shadow.verify_integrity() and len(shadow.chain) >= 5:
        print(f" -> PASSED: Concurrent sequence finalized in SHADOW.")
        return True
    return False

def run_all():
    results = {
        "fail_closed_authority_test": fail_closed_authority_test(),
        "idempotency_replay_test": idempotency_replay_test(),
        "shadow_integrity_break_test": shadow_integrity_break_test(),
        "silvia_adversarial_threshold_test": silvia_adversarial_threshold_test(),
        "concurrent_workflow_collision_test": concurrent_workflow_collision_test()
    }

    print("\n--- RC FINAL TEST MATRIX ---")
    all_passed = True
    for test, passed in results.items():
        print(f"{'[PASS]' if passed else '[FAIL]'} {test}")
        if not passed: all_passed = False

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_all()
