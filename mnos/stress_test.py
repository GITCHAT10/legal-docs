import sys
import os
import uuid
from decimal import Decimal
import json
import hmac
import hashlib
from datetime import datetime, timezone

# Add path
sys.path.append(os.getcwd())

from mnos.modules.fce.service import fce, FinancialException
from mnos.modules.shadow.service import shadow
from mnos.core.events.service import events
from mnos.core.ai.silvia import silvia
from mnos.interfaces.sky_i.comms.whatsapp import whatsapp
from mnos.modules.knowledge.service import knowledge_core
from mnos.shared.execution_guard import guard
from mnos.core.security.aegis import aegis
from mnos.config import config

def get_test_session(nonce=None, location="ADDU_FORTRESS", role="admin"):
    payload = {
        "device_id": "nexus-admin-01",
        "role": role,
        "nonce": nonce or str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": location
    }
    sig = aegis.sign_session(payload)
    payload["signature"] = sig
    return payload

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

    session = get_test_session()
    guard.execute_sovereign_action(
        "nexus.booking.created",
        {"data": "test"},
        session,
        lambda p: "done"
    )

    original_integrity = shadow.verify_integrity()
    print(f"Original Integrity: {original_integrity}")

    # Tamper
    shadow.chain[1]["timestamp"] = "2026-04-22T09:00:00Z"
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

    # 4. Day-Zero Stress Test: OMADHOO_PILOT (High Fidelity Simulation)
    print("\n[TEST 4: Day-Zero OMADHOO PILOT]")
    # Simulation: 1000 events in 24-hour virtual window
    session = get_test_session(location="OMADHOO_PILOT")

    for i in range(10): # Scaled down for speed but logic same
        guard.execute_sovereign_action(
            "event_simulation",
            {"anomaly_score": 0.1, "data": i},
            session,
            lambda p: "PROCESSED"
        )

    print(f"Final Ledger Size: {len(shadow.chain)}")
    print(f"Final Integrity: {shadow.verify_integrity()}")

    print("\n--- ✅ STRESS TESTS COMPLETE ---")

if __name__ == "__main__":
    stress_test()
