from typing import Dict, Optional, Any, List
from sqlalchemy.orm import Session
from mnos.modules.fce import models
import uuid
import hashlib
from datetime import datetime, date, UTC
from .tax_logic import calculate_maldives_taxes
from mnos.modules.shadow import service as shadow_service
from fastapi import HTTPException
from decimal import Decimal

# Mock settings
DUAL_QR_THRESHOLD_MVR = 50000.0
USD_TO_MVR_RATE = 15.42

def _generate_mira_receipt(folio_id: int, total_amount: float, timestamp: datetime) -> str:
    date_str = timestamp.strftime("%Y%m%d")
    folio_hash = hashlib.sha256(str(folio_id).encode()).hexdigest()[:8].upper()
    region_code = "MV"
    return f"MIRA-{date_str}-{folio_hash}-{region_code}"

def finalize_invoice(
    db: Session,
    folio_id: int,
    actor: str,
    qr_authorization_id: Optional[int] = None,
    force_override: bool = False,
    tenant_id: str = "default"
) -> models.Invoice:
    """
    Finalize folio invoice with sovereign compliance.
    """
    folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")

    if folio.status == models.FolioStatus.FINALIZED:
        raise HTTPException(status_code=400, detail="Folio already finalized")

    # 1. Calculate sovereign taxes (MIRA-compliant)
    subtotal = folio.total_amount # Simplified for sandbox
    mira_gst = subtotal * 0.12 # 12% GST

    # Mock Green Tax calculation
    green_tax = 6.0 * 15.42 # Mock 1 night
    total_with_taxes = subtotal + mira_gst + green_tax

    # 2. Dual-QR validation (if amount > threshold)
    if total_with_taxes > DUAL_QR_THRESHOLD_MVR and not force_override:
        if not qr_authorization_id:
            raise HTTPException(status_code=403, detail="Dual-QR authorization required for high-value invoice")

        qr_auth = db.query(models.QRAuthorizationRequest).filter(
            models.QRAuthorizationRequest.id == qr_authorization_id,
            models.QRAuthorizationRequest.status == "AUTHORIZED",
            models.QRAuthorizationRequest.folio_id == folio_id
        ).first()

        if not qr_auth:
            raise HTTPException(status_code=403, detail="Invalid or unauthorized Dual-QR")

    # 3. Update folio
    folio.status = models.FolioStatus.FINALIZED
    folio.finalized_by = actor
    folio.finalized_at = datetime.now(UTC)
    folio.mira_gst_amount = mira_gst
    folio.mira_green_tax_amount = green_tax
    folio.total_amount = total_with_taxes
    folio.qr_authorization_id = str(qr_authorization_id) if qr_authorization_id else None

    folio.mira_receipt_number = _generate_mira_receipt(folio_id, total_with_taxes, folio.finalized_at)

    # 4. Create Invoice
    invoice = models.Invoice(
        tenant_id=tenant_id,
        folio_id=folio_id,
        invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
        total_amount=total_with_taxes
    )
    db.add(invoice)
    db.flush()

    # 5. COMMIT BEFORE SHADOW LOG
    db.commit()
    db.refresh(invoice)

    # 6. Generate SHADOW Audit entry
    shadow_service.commit_evidence(db, invoice.trace_id, {
        "actor": actor,
        "action": "INVOICE_FINALIZED",
        "entity_type": "INVOICE",
        "entity_id": invoice.id,
        "payload": {
            "folio_id": str(folio_id),
            "total": str(total_with_taxes),
            "mira_receipt": folio.mira_receipt_number,
            "dual_qr_used": bool(qr_authorization_id)
        }
    })
    db.commit()

    return invoice

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
