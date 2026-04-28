from sqlalchemy.orm import Session
from uuid import uuid4
from . import models, schemas
from mnos.core.audit.shadow import commit_shadow_evidence
from datetime import datetime, UTC
from fastapi import HTTPException

def finalize_invoice(db: Session, folio_id: int, actor: str) -> dict:
    folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
    if not folio:
        raise ValueError(f"Folio {folio_id} not found")
    if folio.status != models.FolioStatus.OPEN:
        raise ValueError(f"Folio {folio_id} is already {folio.status}")

    # Calculate totals
    base = folio.base_amount or 0.0
    service_charge = round(base * 0.10, 2)
    tgst = round((base + service_charge) * 0.08, 2)
    total = round(base + service_charge + tgst, 2)

    trace_id = str(uuid4())
    invoice = models.Invoice(
        folio_id=folio.id,
        trace_id=trace_id,
        tenant_id=folio.tenant_id,
        invoice_number=f"INV-{uuid4().hex[:8].upper()}",
        total_amount=total
    )
    db.add(invoice)

    # SHADOW audit commit
    commit_shadow_evidence(
        db=db,
        trace_id=trace_id,
        event="invoice_finalized",
        payload={"folio_id": folio.id, "total": total, "actor": actor}
    )

    folio.status = models.FolioStatus.FINALIZED
    db.commit()
    db.refresh(invoice)

    return {
        "id": invoice.id,
        "trace_id": invoice.trace_id,
        "total_amount": invoice.total_amount,
        "status": "finalized"
    }

def open_folio(db: Session, reservation_id: str, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> models.Folio:
    if not trace_id: raise ValueError("trace_id required")
    folio = models.Folio(
        tenant_id=tenant_id,
        trace_id=trace_id,
        external_reservation_id=reservation_id,
        status=models.FolioStatus.OPEN,
        created_by=actor
    )
    db.add(folio)
    db.commit()
    db.refresh(folio)
    return folio

def post_charge(db: Session, folio_id: int, charge_data: dict, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> models.FolioLine:
    folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
    if not folio: raise ValueError(f"Folio {folio_id} not found")

    line = models.FolioLine(
        tenant_id=tenant_id,
        trace_id=trace_id,
        folio_id=folio_id,
        type=charge_data["type"],
        base_amount=charge_data["base_amount"],
        amount=charge_data["base_amount"], # Simplified
        created_by=actor
    )
    db.add(line)
    folio.base_amount += line.base_amount
    db.commit()
    db.refresh(line)
    return line
