import sys
import os
from decimal import Decimal

# Ensure PYTHONPATH includes /app
sys.path.append(os.getcwd())

from mnos.boot_check import check_integrity
from mnos.interfaces.sky_i.comms.whatsapp import whatsapp
from mnos.modules.exmail.service import exmail_authority
from mnos.modules.shadow.service import shadow
from mnos.modules.shadow_sync.service import shadow_sync
from mnos.modules.knowledge.service import knowledge_core
from mnos.core.resilience.backup import resilience

# Import workflows to register subscribers
import mnos.modules.workflows.booking
import mnos.modules.workflows.guest_arrival
import mnos.modules.workflows.emergency

def run_validation():
    print("--- 🏛️ NEXUS ASI SKY-i OS FINAL VALIDATION (ExMAIL ASI) ---")

    # 1. Boot Integrity
    if not check_integrity():
        print("BOOT FAILED. EXITING.")
        return

    # 2. Knowledge Ingestion
    dna = "NEXUS DNA: Bookings are handled by FCE. Arrivals trigger AQUA. Emergencies trigger LIFELINE."
    knowledge_core.ingest("NEXUS_DNA", dna)

    from mnos.core.security.aegis import aegis
    ctx = {
        "user_id": "GUEST-VAL-01",
        "session_id": "SESS-VAL-01",
        "device_id": "nexus-001",
        "issued_at": 1700000000,
        "nonce": "N-VAL-01"
    }
    ctx["signature"] = aegis.sign_session(ctx)

    # 3. ExMAIL Booking (Positive Sentiment -> Task Conversion)
    print("\n[SCENARIO 1: ExMAIL Positive Booking]")
    res_mail1 = exmail_authority.ingest_inbound_exmail(
        "happy.guest@example.com",
        "Booking Request",
        "Good morning, I had a great stay last time and want to book again. Excellent service!",
        ctx
    )
    print(f"Result: {res_mail1['status']} | Sentiment: {res_mail1['sentiment']} | Reply: {res_mail1['smart_reply']}")

    # 4. ExMAIL Emergency (Negative Sentiment -> Ticket Conversion)
    print("\n[SCENARIO 2: ExMAIL Negative Emergency]")
    ctx2 = {
        "user_id": "GUEST-VAL-02",
        "session_id": "SESS-VAL-02",
        "device_id": "nexus-001",
        "issued_at": 1700000000,
        "nonce": "N-VAL-02"
    }
    ctx2["signature"] = aegis.sign_session(ctx2)
    res_mail2 = exmail_authority.ingest_inbound_exmail(
        "angry.guest@example.com",
        "HELP NOW",
        "This is the worst! Everything is slow and failing. SOS EMERGENCY!",
        ctx2
    )
    print(f"Result: {res_mail2['status']} | Sentiment: {res_mail2['sentiment']} | Reply: {res_mail2['smart_reply']}")

    # 5. Audit & Persistence
    print("\n[AUDIT: SHADOW LEDGER]")
    print(f"Ledger Size: {len(shadow.chain)} entries")
    print(f"Integrity: {'OK' if shadow.verify_integrity() else 'CORRUPT'}")

    # 6. Resilience
    print("\n[RESILIENCE]")
    snap = resilience.create_snapshot()
    resilience.validate_restore(snap)

    print("\n--- ✅ VALIDATION COMPLETE ---")

if __name__ == "__main__":
    run_validation()
