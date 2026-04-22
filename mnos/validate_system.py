import sys
import os
from decimal import Decimal

# Ensure PYTHONPATH includes /app
sys.path.append(os.getcwd())

from mnos.boot_check import check_integrity
from mnos.interfaces.sky_i.comms.whatsapp import whatsapp
from mnos.modules.email.service import email_authority
from mnos.modules.shadow.service import shadow
from mnos.modules.knowledge.service import knowledge_core
from mnos.core.resilience.backup import resilience

# Import workflows to register subscribers
import mnos.modules.workflows.booking
import mnos.modules.workflows.guest_arrival
import mnos.modules.workflows.emergency

def run_validation():
    print("--- 🏛️ NEXUS ASI SKY-i OS FINAL VALIDATION (with Email Intelligence) ---")

    # 1. Boot Integrity
    if not check_integrity():
        print("BOOT FAILED. EXITING.")
        return

    # 2. Knowledge Ingestion
    dna = "NEXUS DNA: Bookings are handled by FCE. Arrivals trigger AQUA. Emergencies trigger LIFELINE."
    knowledge_core.ingest("NEXUS_DNA", dna)

    ctx = {"device_id": "nexus-001", "bound_device_id": "nexus-001"}

    # 3. WhatsApp Booking
    print("\n[SCENARIO 1: WhatsApp Booking]")
    res1 = whatsapp.receive_message("+9601112222", "I want to book a room", ctx)
    print(f"Result: {res1['status']} | Response: {res1.get('response')}")

    # 4. Email Booking (New Module)
    print("\n[SCENARIO 2: Email Booking]")
    res_mail = email_authority.ingest_inbound_email(
        "guest@example.com",
        "Room Reservation Request",
        "Dear SKY-i, I would like to book a room for next week.",
        ctx
    )
    print(f"Result: {res_mail['status']} | Smart Reply: {res_mail.get('smart_reply')}")

    # 5. WhatsApp Guest Arrival
    print("\n[SCENARIO 3: Guest Arrival]")
    res2 = whatsapp.receive_message("+9601112222", "I have arrived at the airport", ctx)
    print(f"Result: {res2['status']} | Response: {res2.get('response')}")

    # 6. WhatsApp Emergency
    print("\n[SCENARIO 4: Emergency SOS]")
    res3 = whatsapp.receive_message("+9601112222", "SOS! EMERGENCY!", ctx)
    print(f"Result: {res3['status']} | Response: {res3.get('response')}")

    # 7. Audit & Persistence
    print("\n[AUDIT: SHADOW LEDGER]")
    print(f"Ledger Size: {len(shadow.chain)} entries")
    print(f"Integrity: {'OK' if shadow.verify_integrity() else 'CORRUPT'}")

    # 8. Resilience
    print("\n[RESILIENCE]")
    snap = resilience.create_snapshot()
    resilience.validate_restore(snap)

    print("\n--- ✅ VALIDATION COMPLETE ---")

if __name__ == "__main__":
    run_validation()
