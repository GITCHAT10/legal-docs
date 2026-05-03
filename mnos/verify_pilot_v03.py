import os
import sys
from decimal import Decimal

# Ensure mnos is in path
sys.path.append(os.getcwd())

# Mock environment
os.environ["NEXGEN_SECRET"] = "verified_secret"

from mnos.modules.legal.lawyer_login import lawyer_login
from mnos.modules.legal.bar_registry import bar_registry
from mnos.modules.integrations.business_portal import business_portal
from mnos.modules.aegis.brand_context import brand_context
from mnos.modules.research.mvlaw_source import mvlaw_source
from mnos.modules.research.sovereign_rag import sovereign_rag
from mnos.modules.legal.fce_legal_anchor import FceLegalAnchor
from mnos.modules.legal.tenancy_notice import tenancy_notice
from mnos.integrations.mira.tgst_mock import mira_tgst
from mnos.modules.legal.affidavit_generator import affidavit_generator
from mnos.modules.shadow.service import shadow

def run_pilot_verification():
    print("--- eLEGAL v0.3 PILOT VERIFICATION START ---")

    # 1. Lawyer Login & Bar Council Check
    print("\n[1/7] Testing Lawyer Login (eFaas -> Bar Council)...")
    login = lawyer_login.login("TOKEN-123", "LICENSED_LAWYER", "SALA_HOTELS", "L-9982", "HW-ID-001")
    print(f"Result: {login}")

    # 2. Brand Context Namespace
    print("\n[2/7] Testing Brand Context Switch...")
    trace = brand_context.set_brand_context("97_DEGREES_EAST")
    print(f"Trace: {trace}")

    # 3. MVLAW Research
    print("\n[3/7] Testing MVLAW Research...")
    research = mvlaw_source.ingest_regulation("REG-LAND-2024")
    print(f"Ingested: {research['id']} - Status: {research['status']}")
    rag = sovereign_rag.analyze("Lease terms", [research['hash']])
    print(f"RAG Analysis: {rag['status']}")

    # 4. FCE Legal Anchor & Shortfall
    print("\n[4/7] Testing FCE Legal Anchor Shortfall...")
    anchor = FceLegalAnchor("MATTER-001", "ANCHOR-PILOT", "SALA_HOTELS", "1166708")
    anchor.amount_due = Decimal("5000.00")
    sync = anchor.sync_fce(Decimal("4500.00"))
    print(f"Sync Result: {sync['reconciliation_status']} - Balance: {sync['outstanding_balance']}")

    # 5. Tenancy Notice Flow
    print("\n[5/7] Testing Tenancy Notice Flow...")
    notice = tenancy_notice.generate_draft_notice("LEASE-99", 500.0)
    print(f"Draft Notice: {notice['status']}")
    approval = tenancy_notice.approve_notice("NOTICE-001", "LAWYER-L-9982")
    print(f"Approved: {approval['status']} for {approval['delivery_mode']}")

    # 6. MIRA Mock Receipt
    print("\n[6/7] Testing MIRA TGST Mock Filing...")
    receipt = mira_tgst.file_tgst_mock("1166708", "2024-Q1", 425.0, sync['shadow_hash'])
    print(f"MIRA Receipt: {receipt['mira_receipt_no']}")

    # 7. Affidavit Bundle
    print("\n[7/7] Generating Affidavit Bundle...")
    bundle = affidavit_generator.generate_affidavit_bundle("MATTER-001", ["evidence_doc_1"])
    print(f"Bundle: {bundle['status']} - Verified via SHADOW Hash: {bundle['shadow_verification_hash']}")

    print("\nVerifying SHADOW Ledger Integrity...")
    if shadow.verify_integrity():
        print("SHADOW Integrity: VERIFIED")
    else:
        print("SHADOW Integrity: FAILED")
        sys.exit(1)

    print("\n--- eLEGAL v0.3 PILOT VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    run_pilot_verification()
