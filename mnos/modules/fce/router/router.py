from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mnos.core.api import deps
from mnos.modules.fce import schemas, models, tax_logic, service

router = APIRouter()

@router.post("/folios", response_model=schemas.Folio)
def create_folio(
    *,
    db: Session = Depends(deps.get_db),
    reservation_id: str,
    trace_id: str,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    if not trace_id:
        raise HTTPException(status_code=400, detail="trace_id is mandatory")
    return service.open_folio(db, reservation_id, trace_id)

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

@router.post("/charges", response_model=schemas.Charge)
def post_charge(
    *,
    db: Session = Depends(deps.get_db),
    charge_in: schemas.ChargeCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    if not charge_in.trace_id:
        raise HTTPException(status_code=400, detail="trace_id is mandatory")
    charge_data = charge_in.model_dump()
    return service.post_charge(db, charge_in.folio_id, charge_data, charge_in.trace_id)

@router.post("/payments", response_model=schemas.Payment)
def post_payment(
    *,
    db: Session = Depends(deps.get_db),
    payment_in: schemas.PaymentCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    if not payment_in.trace_id:
        raise HTTPException(status_code=400, detail="trace_id is mandatory")
    payment_data = payment_in.model_dump()
    return service.process_payment(db, payment_in.folio_id, payment_data, payment_in.trace_id)
