from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mnos.core.api import deps
from mnos.modules.fce import schemas, models, service, mira_export, edge_cases

router = APIRouter()

@router.post("/folios", response_model=schemas.Folio)
def open_folio(
    *,
    db: Session = Depends(deps.get_db),
    folio_in: schemas.FolioCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return service.open_folio(db, reservation_id=folio_in.external_reservation_id, trace_id=folio_in.trace_id, tenant_id=folio_in.tenant_id, actor=current_user.email)

@router.get("/folios/{folio_id}", response_model=schemas.Folio)
def read_folio(
    folio_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")
    return folio

@router.post("/folios/{folio_id}/charges", response_model=schemas.FolioLine)
def post_charge(
    folio_id: int,
    charge_in: schemas.FolioLineCreate,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    charge_data = charge_in.dict()
    return service.post_charge(db, folio_id=folio_id, charge_data=charge_data, trace_id=charge_in.trace_id, tenant_id=charge_in.tenant_id, actor=current_user.email)

@router.post("/folios/{folio_id}/payments", response_model=schemas.FolioTransaction)
def post_transaction(
    folio_id: int,
    transaction_in: schemas.FolioTransactionBase,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    transaction_data = transaction_in.dict()
    return service.post_transaction(db, folio_id=folio_id, payment_data=transaction_data, trace_id=transaction_in.trace_id, tenant_id=transaction_in.tenant_id, actor=current_user.email)

@router.post("/folios/{folio_id}/finalize", response_model=schemas.Invoice)
def finalize_invoice(
    folio_id: int,
    trace_id: str,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return service.finalize_invoice(db, folio_id=folio_id, trace_id=trace_id, actor=current_user.email)

@router.post("/lines/{line_id}/void", response_model=schemas.FolioLine)
def void_charge(
    line_id: int,
    reason: str,
    trace_id: str,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Explicit Reversal Doctrine: Linked Counter-Entry."""
    return edge_cases.void_charge(db, line_id=line_id, reason=reason, trace_id=trace_id, actor=current_user.email)

@router.get("/invoices/{invoice_id}/mira-export", response_model=Dict[str, Any])
def get_mira_export(
    invoice_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """MIRAconnect Hash-Verified JSON Export."""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return mira_export.export_mira_json(invoice)

@router.get("/summary", response_model=Any)
def get_finance_summary(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
):
    from sqlalchemy import func
    folio_counts = db.query(models.Folio.status, func.count(models.Folio.id)).group_by(models.Folio.status).all()
    total_rev = db.query(func.sum(models.Folio.total_amount)).scalar() or 0.0

    return {
        "folio_status_counts": {status.value: count for status, count in folio_counts},
        "total_revenue_recognized": total_rev
    }
