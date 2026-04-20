from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mnos.core.api import deps
from mnos.modules.fce import schemas, models, service

router = APIRouter()

@router.post("/folios", response_model=schemas.Folio)
def open_folio(
    *,
    db: Session = Depends(deps.get_db),
    folio_in: schemas.FolioCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return service.open_folio(db, reservation_id=folio_in.external_reservation_id, trace_id=folio_in.trace_id)

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
    return service.post_charge(db, folio_id=folio_id, charge_data=charge_data, trace_id=charge_in.trace_id)

@router.post("/folios/{folio_id}/finalize", response_model=schemas.Invoice)
def finalize_invoice(
    folio_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return service.finalize_invoice(db, folio_id=folio_id)
