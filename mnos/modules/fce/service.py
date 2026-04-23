from typing import Dict, Optional, Any, List
from sqlalchemy.orm import Session
from mnos.modules.fce import models
import uuid
from datetime import datetime, date, UTC
from .tax_logic import calculate_maldives_taxes
from mnos.modules.shadow import service as shadow_service
from fastapi import HTTPException

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

def finalize_invoice(db: Session, folio_id: int, trace_id: Optional[str] = None, tenant_id: str = "default", actor: str = "SYSTEM") -> models.Invoice:
    """
    Harden Finance: Lock exchange rate and generate ledger entry.
    Law: Base + 10% SC -> Subtotal -> 17% TGST.
    """
    try:
        if not trace_id:
            trace_id = f"INV-FIN-{uuid.uuid4().hex[:8]}"

        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio:
            raise HTTPException(status_code=404, detail="Folio not found")

        # idempotency / guard against double-finalization
        if folio.status == models.FolioStatus.FINALIZED:
            existing_invoice = db.query(models.Invoice).filter(models.Invoice.folio_id == folio_id).first()
            if existing_invoice:
                return existing_invoice

        # 1. Lock Exchange Rate (Mock for sandbox)
        exchange_rate = 15.42 # USD/MVR

        # 2. Update Folio Status
        folio.status = models.FolioStatus.FINALIZED

        # 3. Create Invoice
        invoice = models.Invoice(
            tenant_id=tenant_id,
            trace_id=trace_id,
            folio_id=folio_id,
            invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
            total_amount=folio.total_amount
        )
        db.add(invoice)
        db.flush()

        # 4. Generate SHADOW Audit entry
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "FINALIZE_INVOICE",
            "entity_type": "INVOICE",
            "entity_id": invoice.id,
            "financial_lock": {
                "amount": invoice.total_amount,
                "exchange_rate": exchange_rate,
                "currency": folio.currency
            }
        })

        db.commit()
        db.refresh(invoice)
        return invoice
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise e

def post_charge(db: Session, folio_id: int, charge_data: Dict, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> models.FolioLine:
    try:
        if not trace_id: raise ValueError("trace_id required")
        existing = db.query(models.FolioLine).filter(models.FolioLine.trace_id == trace_id, models.FolioLine.tenant_id == tenant_id).first()
        if existing: return existing

        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio: raise ValueError(f"Folio {folio_id} not found")

        biz_date = charge_data.get("business_date")
        if isinstance(biz_date, str): biz_date = date.fromisoformat(biz_date)
        elif not biz_date: biz_date = date.today()

        # ENFORCEMENT: 10% Service Charge + 17% TGST (tourism flows)
        taxes = calculate_maldives_taxes(
            charge_data["base_amount"],
            biz_date,
            charge_data.get("apply_green_tax", False),
            charge_data.get("nights", 0)
        )

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

        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "POST_TRANSACTION",
            "entity_type": "FOLIO_TRANSACTION",
            "entity_id": transaction.id,
            "before_state": before_state,
            "after_state": {"amount": transaction.amount, "folio_paid": folio.paid_amount}
        })

        db.commit()
        db.refresh(transaction)
        return transaction
    except Exception:
        db.rollback()
        raise
