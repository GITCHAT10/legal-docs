import os
import sys
from decimal import Decimal

# Ensure mnos is in path
sys.path.append(os.getcwd())

# Mock environment variable
os.environ["NEXGEN_SECRET"] = "verification_secret_123"

from mnos.modules.elegal.ledger import elegal_ledger
from mnos.modules.elegal.pulse import elegal_pulse
from mnos.modules.elegal.patents import elegal_patents
from mnos.modules.elegal.cases import matter_manager, CaseCategory, CaseStatus
from mnos.modules.elegal.clients import client_manager
from mnos.modules.elegal.finance import legal_finance
from mnos.modules.elegal.documents import document_manager
from mnos.modules.elegal.packs.tenancy import tenancy_engine
from mnos.modules.elegal.packs.tenancy_finance import tenancy_finance
from mnos.modules.elegal.packs.tenancy_notices import tenancy_notices
from mnos.modules.shadow.service import shadow

def run_verification():
    print("--- eLEGAL ASI CORE VERIFICATION START ---")

    # 1. Verify Ledger
    print("\n[1/7] Testing eLEGAL Ledger Reconcilliation...")
    ledger_result = elegal_ledger.reconcile_trust_account(
        client_id="C-SALA-001",
        trust_balance=Decimal("50000.00"),
        taxable_income=Decimal("15000.00")
    )
    print(f"Result: {ledger_result}")

    # 2. Verify Pulse
    print("\n[2/7] Testing eLEGAL Pulse AI Interface...")
    from mnos.modules.knowledge.service import knowledge_core
    knowledge_core.ingest("legal_docs", "Sala Hotels follows standard resort employment regulations in the Maldives.")

    pulse_result = elegal_pulse.process_legal_query("Sala Hotels", "What are the employment regulations?")
    print(f"Result: {pulse_result}")

    # 3. Verify Case Management
    print("\n[3/7] Testing Case Management (InfixAdvocate adoption)...")
    case = matter_manager.create_case("CASE-001", "Resort Lease Dispute", CaseCategory.LAND, "C-SALA-001")
    print(f"Case Created: {case['case_id']} - {case['status']}")
    matter_manager.schedule_hearing("CASE-001", "2024-05-15", "Courtroom 4")
    print(f"Hearing Scheduled: {case['hearings'][-1]}")

    # 4. Verify Client Management
    print("\n[4/7] Testing Client Management...")
    client = client_manager.register_client("C-97E-001", "97 Degrees East", "97 Degrees East", "contact@97east.mv")
    print(f"Client Registered: {client['name']}")
    app = client_manager.schedule_appointment("C-97E-001", "2024-04-25", "Legal Review")
    print(f"Appointment Scheduled: {app['date']} for {app['purpose']}")

    # 5. Verify Legal Finance
    print("\n[5/7] Testing Legal Finance & Billing...")
    invoice = legal_finance.generate_invoice("C-SALA-001", Decimal("2500.00"), "Legal Advisory Fees")
    print(f"Invoice Generated: {invoice['invoice_id']} - Total: {invoice['tax_details']['taxable_income']}")
    summary = legal_finance.get_financial_summary()
    print(f"Financial Summary: {summary}")

    # 6. Verify Document Management
    print("\n[6/7] Testing Document Generation (Resort Portfolio)...")
    doc = document_manager.generate_document("Employment Contract", "Sala Hotels", {"employee": "Ahmed", "role": "Manager"})
    print(f"Document Generated: {doc['doc_id']} - {doc['status']}")
    signed_doc = document_manager.sign_document(doc["doc_id"], "CEO-MIG")
    print(f"Document Signed: {signed_doc['doc_id']} by {signed_doc['signed_by']}")

    # 7. Verify Tenancy Pack (IMXON)
    print("\n[7/8] Testing Maldives Tenancy Pack (IMXON)...")
    lease = tenancy_engine.create_lease("LANDLORD-001", "TENANT-001", "PROP-MAL-99", 1500.0, 3000.0)
    print(f"Lease Created: {lease['lease_id']} bound to {lease['anchor_id']}")

    payment = tenancy_finance.process_rent_payment(lease["lease_id"], Decimal("1500.00"))
    print(f"Rent Payment Processed: {payment['amount']} USD - Folio Total: {payment['folio']['total']}")

    notice = tenancy_notices.issue_late_rent_notice(lease["lease_id"], 5)
    print(f"Late Rent Notice: {notice['type']} issued.")

    # 8. Verify Patents
    print("\n[8/8] Testing Patentable MOATS...")
    p1 = elegal_patents.sovereign_contextual_ingestion({"title": "New Resort Lease Regulation 2024", "date": "2024-04-20"})
    print(f"   P1 Result: {p1['status']}")
    p2 = elegal_patents.multi_brand_ip_sentry("fushigili", {"source": "fake-fushigili-domain.com"})
    print(f"   P2 Result: {p2['action_taken']}")
    p3 = elegal_patents.predictive_litigation_asi({"id": "LIT-2024-001", "type": "Contract Dispute"})
    print(f"   P3 Result: Probability {p3['success_probability']}%")

    # Final Integrity Check
    print("\nVerifying SHADOW Ledger Integrity...")
    if shadow.verify_integrity():
        print("SHADOW Integrity: VERIFIED")
    else:
        print("SHADOW Integrity: FAILED")
        sys.exit(1)

    print("\n--- eLEGAL ASI CORE VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    run_verification()
