import pytest
from mnos.modules.airbox.engine import AirBoxEngine
from mnos.modules.sigdoc.engine import SigDocEngine
from mnos.modules.finance.invoice import FceInvoiceEngine
from main import shadow_core, fce_core, events_core, guard

def test_no_event_no_invoice():
    """Rule: Blocking invoices without verified delivery events."""
    invoice_engine = FceInvoiceEngine(fce_core, shadow_core, events_core)
    actor_ctx = {"identity_id": "STAFF-01", "role": "staff"}

    delivery_data = {
        "delivery_id": "FAKE-EVENT-ID",
        "total_base": 5000
    }

    with pytest.raises(PermissionError, match="FAIL CLOSED: No verified delivery event"):
        with guard.sovereign_context(actor_ctx):
            invoice_engine.generate_sovereign_invoice(actor_ctx, delivery_data)

def test_verified_delivery_to_invoice():
    """Rule: Invoice generated successfully after verified delivery."""
    invoice_engine = FceInvoiceEngine(fce_core, shadow_core, events_core)
    actor_ctx = {"identity_id": "STAFF-01", "role": "staff"}
    event_id = "VERIFIED-DEL-101"

    # Register the event
    invoice_engine.register_delivery_event(event_id)

    delivery_data = {
        "delivery_id": event_id,
        "total_base": 10000,
        "category": "RESORT_SUPPLY"
    }

    with guard.sovereign_context(actor_ctx):
        invoice = invoice_engine.generate_sovereign_invoice(actor_ctx, delivery_data)

    assert invoice["status"] == "SEALED"
    # Pricing: 10000 + 1000 (SC) = 11000. 11000 * 0.17 (TGST) = 1870. Total = 12870.
    assert invoice["pricing"]["total"] == 12870.0
    assert invoice["pricing"]["tax_amount"] == 1870.0

def test_shadow_audit_trail():
    """Verify that every major step is recorded in the SHADOW ledger."""
    airbox = AirBoxEngine(shadow_core)
    sigdoc = SigDocEngine(shadow_core)
    actor_id = "STAFF-02"

    initial_chain_len = len(shadow_core.chain)

    with guard.sovereign_context():
        # 1. OCR Process
        ocr_res = airbox.process_waybill_image(actor_id, "waybill_001.jpg")

        # 2. SigDoc Seal
        seal = sigdoc.seal_document(actor_id, "WAYBILL", ocr_res["data"])

    assert len(shadow_core.chain) == initial_chain_len + 2
    assert shadow_core.chain[-2]["event_type"] == "airbox.ocr.processed"
    assert shadow_core.chain[-1]["event_type"] == "sigdoc.sealed.WAYBILL"
    assert shadow_core.verify_integrity() is True

from decimal import Decimal

def test_mira_2026_tax_rules():
    """Verify strict adherence to MIRA 2026 billing rules."""
    # Tourism category: 10% SC, 17% TGST
    res = fce_core.calculate_local_order(Decimal("100.0"), "TOURISM")
    # 100 + 10 (SC) = 110. 110 * 0.17 = 18.7. Total = 128.7
    assert res["service_charge"] == 10.0
    assert res["tax_amount"] == 18.7
    assert res["total"] == 128.7

    # Retail category: 10% SC, 8% GST
    res = fce_core.calculate_local_order(Decimal("100.0"), "RETAIL")
    # 100 + 10 (SC) = 110. 110 * 0.08 = 8.8. Total = 118.8
    assert res["service_charge"] == 10.0
    assert res["tax_amount"] == 8.8
    assert res["total"] == 118.8
