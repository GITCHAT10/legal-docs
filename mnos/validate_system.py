import sys
import os
from decimal import Decimal

# Ensure PYTHONPATH includes /app
sys.path.append(os.getcwd())

from datetime import datetime, timezone
from mnos.boot_check import check_integrity
from mnos.core.security.aegis import aegis
from mnos.interfaces.sky_i.comms.whatsapp import whatsapp
from mnos.modules.exmail.service import exmail_authority
from mnos.modules.shadow.service import shadow
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

    # SECURE: All contexts must be signed before execution
    def get_signed_ctx(session_id):
        ctx_payload = {
            "device_id": "nexus-001",
            "nonce": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        ctx = ctx_payload.copy()
        ctx["signature"] = aegis.sign_context(ctx_payload)
        return ctx

    ctx1 = get_signed_ctx("SESSION-001")

    # 3. ExMAIL Booking (Positive Sentiment -> Task Conversion)
    print("\n[SCENARIO 1: ExMAIL Positive Booking]")
    res_mail1 = exmail_authority.ingest_inbound_exmail(
        "happy.guest@example.com",
        "Booking Request",
        "Good morning, I had a great stay last time and want to book again. Excellent service!",
        ctx1
    )
    print(f"Result: {res_mail1['status']} | Sentiment: {res_mail1['sentiment']} | Reply: {res_mail1['smart_reply']}")

    # 4. ExMAIL Emergency (Negative Sentiment -> Ticket Conversion)
    ctx2 = get_signed_ctx("SESSION-002")
    print("\n[SCENARIO 2: ExMAIL Negative Emergency]")
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
    integrity_ok = shadow.verify_integrity()
    print(f"Integrity: {'OK' if integrity_ok else 'CORRUPT'}")

    # 6. Forensic Bundle Export
    print("\n[FORENSIC REPORT]")
    report = shadow.export_forensic_bundle()
    print(f"Generated GUARD_PROOF_REPORT.json | Hardening: {report['hardening_version']}")

    # 7. Final Output & Compliance
    if not integrity_ok:
        print("\n!!! VALIDATION FAILED: Ledger compromised.")
        sys.exit(1)

    print("\nMARS RECON Genesis Node v9.5 = HARDENED")
    print("\n--- ✅ VALIDATION COMPLETE ---")

if __name__ == "__main__":
    try:
        run_validation()
    except Exception as e:
        print(f"\n!!! SYSTEM HALT: Validation Error: {e}")
        sys.exit(1)
