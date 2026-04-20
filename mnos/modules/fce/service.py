from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from mnos.modules.fce import models
import uuid
from datetime import datetime
from .services.tax_service import calculate_maldives_tax
from .services.finance_service import get_next_invoice_number, verify_period_open
from mnos.modules.shadow import service as shadow_service

def open_folio(db: Session, reservation_id: str, trace_id: str, actor: str = "SYSTEM") -> models.Folio:
    try:
        existing = db.query(models.Folio).filter(models.Folio.trace_id == trace_id).first()
        if existing:
            return existing

        folio = models.Folio(
            external_reservation_id=reservation_id,
            trace_id=trace_id,
            status=models.FolioStatus.OPEN
        )
        db.add(folio)
        db.flush()

        # Shadow Evidence
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "OPEN_FOLIO",
            "entity_type": "FOLIO",
            "entity_id": folio.id,
            "after_state": {"reservation_id": reservation_id, "status": folio.status}
        })

        db.commit()
        db.refresh(folio)
        return folio
    except Exception:
        db.rollback()
        raise

def post_charge(db: Session, folio_id: int, charge_data: Dict, trace_id: str, actor: str = "SYSTEM") -> models.FolioLine:
    try:
        # Verify period is open
        posting_date = charge_data.get("business_date", datetime.utcnow().date())
        verify_period_open(db, posting_date)

        existing = db.query(models.FolioLine).filter(models.FolioLine.trace_id == trace_id).first()
        if existing:
            return existing

        taxes = calculate_maldives_tax(
            charge_data["base_amount"],
            charge_data.get("apply_green_tax", False),
            charge_data.get("nights", 0)
        )

        line = models.FolioLine(
            folio_id=folio_id,
            trace_id=trace_id,
            type=charge_data["type"],
            base_amount=taxes["base_amount"],
            service_charge=taxes["service_charge"],
            tgst=taxes["tgst"],
            green_tax=taxes["green_tax"],
            amount=taxes["total_amount"],
            description=charge_data.get("description")
        )
        db.add(line)

        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio:
            raise ValueError(f"Folio {folio_id} not found")

        if folio.status == models.FolioStatus.FINALIZED:
            raise ValueError("Cannot post charge to finalized folio")

        before_state = {"total_amount": folio.total_amount}
        folio.total_amount += line.amount
        db.add(folio)

        # Record in ledger
        ledger = models.LedgerEntry(
            trace_id=f"ledger-{trace_id}",
            account_code="REVENUE",
            credit=line.amount,
            description=f"Charge for folio {folio_id}"
        )
        db.add(ledger)

        db.flush()

        # Shadow Evidence
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "POST_CHARGE",
            "entity_type": "FOLIO_LINE",
            "entity_id": line.id,
            "before_state": before_state,
            "after_state": {"amount": line.amount, "folio_total": folio.total_amount}
        })

        db.commit()
        db.refresh(line)
        return line
    except Exception:
        db.rollback()
        raise

def post_payment(db: Session, folio_id: int, payment_data: Dict, trace_id: str, actor: str = "SYSTEM") -> models.Payment:
    try:
        existing = db.query(models.Payment).filter(models.Payment.trace_id == trace_id).first()
        if existing:
            return existing

        payment = models.Payment(
            folio_id=folio_id,
            trace_id=trace_id,
            amount=payment_data["amount"],
            method=payment_data["method"],
            status=payment_data.get("status", models.PaymentStatus.PAID)
        )
        db.add(payment)

        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio:
            raise ValueError(f"Folio {folio_id} not found")

        before_state = {"paid_amount": folio.paid_amount}
        folio.paid_amount += payment.amount
        db.add(folio)

        db.flush()

        # Shadow Evidence
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "POST_PAYMENT",
            "entity_type": "PAYMENT",
            "entity_id": payment.id,
            "before_state": before_state,
            "after_state": {"amount": payment.amount, "folio_paid": folio.paid_amount}
        })

        db.commit()
        db.refresh(payment)
        return payment
    except Exception:
        db.rollback()
        raise

def finalize_invoice(db: Session, folio_id: int, actor: str = "SYSTEM") -> models.Invoice:
    try:
        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio:
            raise ValueError("Folio not found")

        if folio.status == models.FolioStatus.FINALIZED:
            inv = db.query(models.Invoice).filter(models.Invoice.folio_id == folio_id).first()
            if inv: return inv

        invoice_no = get_next_invoice_number(db)

        invoice = models.Invoice(
            folio_id=folio_id,
            invoice_number=invoice_no,
            total_amount=folio.total_amount,
            tax_summary={
                "sc": sum(l.service_charge for l in folio.lines if not l.is_reversed),
                "tgst": sum(l.tgst for l in folio.lines if not l.is_reversed),
                "green_tax": sum(l.green_tax for l in folio.lines if not l.is_reversed)
            }
        )
        db.add(invoice)

        before_status = folio.status
        folio.status = models.FolioStatus.FINALIZED
        db.add(folio)

        trace_id = f"FINALIZE-{uuid.uuid4().hex[:8]}"

        db.flush()

        # Shadow Evidence
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "FINALIZE_FOLIO",
            "entity_type": "INVOICE",
            "entity_id": invoice.id,
            "before_state": {"status": before_status},
            "after_state": {"status": folio.status, "invoice_number": invoice_no}
        })

        db.commit()
        db.refresh(invoice)
        return invoice
    except Exception:
        db.rollback()
        raise
