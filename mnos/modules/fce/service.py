from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from mnos.modules.fce import models
import uuid
from datetime import datetime
from .services.tax_service import calculate_folio_charge
from .services.finance_service import get_next_invoice_number, verify_period_open
from mnos.modules.shadow import service as shadow_service
from mnos.core.events.dispatcher import event_dispatcher

def _genesis_audit_lock(db: Session, trace_id: str, payload: Dict, actor: str):
    """
    Fail-Closed Audit Gate.
    If SHADOW commit fails, the entire transaction MUST rollback.
    """
    try:
        shadow_service.commit_evidence(db, trace_id, payload)
    except Exception as e:
        # Genesis Lock: If we can't audit it, we can't do it.
        raise RuntimeError(f"Genesis Lock Triggered: SHADOW unreachable for trace {trace_id}. {str(e)}")

def open_folio(db: Session, reservation_id: str, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> models.Folio:
    try:
        if not trace_id: raise ValueError("trace_id required")
        existing = db.query(models.Folio).filter(models.Folio.trace_id == trace_id, models.Folio.tenant_id == tenant_id).first()
        if existing: return existing

        folio = models.Folio(
            tenant_id=tenant_id,
            trace_id=trace_id,
            external_reservation_id=reservation_id,
            status=models.FolioStatus.OPEN,
            created_by=actor
        )
        db.add(folio)
        db.flush()

        # Mandatory Audit Lock
        _genesis_audit_lock(db, trace_id, {
            "actor": actor,
            "action": "OPEN_FOLIO",
            "entity_type": "FOLIO",
            "entity_id": folio.id,
            "after_state": {"reservation_id": reservation_id, "status": folio.status}
        }, actor)

        db.commit()
        db.refresh(folio)
        return folio
    except Exception:
        db.rollback()
        raise

def post_charge(db: Session, folio_id: int, charge_data: Dict, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> models.FolioLine:
    try:
        if not trace_id: raise ValueError("trace_id required")
        existing = db.query(models.FolioLine).filter(models.FolioLine.trace_id == trace_id, models.FolioLine.tenant_id == tenant_id).first()
        if existing: return existing

        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio: raise ValueError(f"Folio {folio_id} not found")
        if folio.status == models.FolioStatus.FINALIZED: raise ValueError("Folio finalized")

        posting_date = charge_data.get("business_date", datetime.utcnow().date())
        verify_period_open(db, posting_date)

        taxes = calculate_folio_charge(db, folio_id, charge_data)

        line = models.FolioLine(
            tenant_id=tenant_id,
            trace_id=trace_id,
            folio_id=folio_id,
            type=charge_data["type"],
            base_amount=taxes["base_amount"],
            service_charge=taxes["service_charge"],
            tgst=taxes["tgst"],
            green_tax=taxes["green_tax"],
            amount=taxes["total_amount"],
            description=charge_data.get("description"),
            created_by=actor
        )
        db.add(line)

        before_state = {"total_amount": folio.total_amount}
        folio.total_amount += line.amount
        db.add(folio)

        db.flush()

        # Mandatory Audit Lock
        _genesis_audit_lock(db, trace_id, {
            "actor": actor,
            "action": "POST_CHARGE",
            "entity_type": "FOLIO_LINE",
            "entity_id": line.id,
            "before_state": before_state,
            "after_state": {"amount": line.amount, "folio_total": folio.total_amount}
        }, actor)

        db.commit()
        db.refresh(line)
        return line
    except Exception:
        db.rollback()
        raise

def post_transaction(db: Session, folio_id: int, payment_data: Dict, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> models.FolioTransaction:
    try:
        if not trace_id: raise ValueError("trace_id required")
        existing = db.query(models.FolioTransaction).filter(models.FolioTransaction.trace_id == trace_id, models.FolioTransaction.tenant_id == tenant_id).first()
        if existing: return existing

        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio: raise ValueError(f"Folio {folio_id} not found")

        transaction = models.FolioTransaction(
            tenant_id=tenant_id,
            trace_id=trace_id,
            folio_id=folio_id,
            amount=payment_data["amount"],
            method=payment_data["method"],
            status=models.TransactionStatus.POSTED,
            created_by=actor
        )
        db.add(transaction)

        before_state = {"paid_amount": folio.paid_amount}
        folio.paid_amount += transaction.amount
        db.add(folio)
        db.flush()

        # Mandatory Audit Lock
        _genesis_audit_lock(db, trace_id, {
            "actor": actor,
            "action": "POST_TRANSACTION",
            "entity_type": "FOLIO_TRANSACTION",
            "entity_id": transaction.id,
            "before_state": before_state,
            "after_state": {"amount": transaction.amount, "folio_paid": folio.paid_amount}
        }, actor)

        db.commit()
        db.refresh(transaction)
        return transaction
    except Exception:
        db.rollback()
        raise

def finalize_invoice(db: Session, folio_id: int, tenant_id: str = "default", actor: str = "SYSTEM") -> models.Invoice:
    try:
        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio: raise ValueError("Folio not found")

        if folio.status == models.FolioStatus.FINALIZED:
            inv = db.query(models.Invoice).filter(models.Invoice.folio_id == folio_id).first()
            if inv: return inv

        invoice_no = get_next_invoice_number(db)
        trace_id = f"FIN-{uuid.uuid4().hex[:8]}"

        invoice = models.Invoice(
            tenant_id=tenant_id,
            trace_id=trace_id,
            folio_id=folio_id,
            invoice_number=invoice_no,
            total_amount=folio.total_amount,
            tax_summary={
                "sc": sum(l.service_charge for l in folio.lines if not l.is_reversed),
                "tgst": sum(l.tgst for l in folio.lines if not l.is_reversed),
                "green_tax": sum(l.green_tax for l in folio.lines if not l.is_reversed)
            },
            created_by=actor
        )
        db.add(invoice)

        before_status = folio.status
        folio.status = models.FolioStatus.FINALIZED
        db.add(folio)
        db.flush()

        # Mandatory Audit Lock
        _genesis_audit_lock(db, trace_id, {
            "actor": actor,
            "action": "FINALIZE_FOLIO",
            "entity_type": "INVOICE",
            "entity_id": invoice.id,
            "before_state": {"status": before_status},
            "after_state": {"status": folio.status, "invoice_number": invoice_no}
        }, actor)

        db.commit()
        db.refresh(invoice)
        return invoice
    except Exception:
        db.rollback()
        raise
