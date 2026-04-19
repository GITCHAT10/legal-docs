from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mnos.core.api import deps
from mnos.modules.fce import schemas, models, tax_logic

router = APIRouter()

@router.post("/folios", response_model=schemas.Folio)
def create_folio(
    *,
    db: Session = Depends(deps.get_db),
    reservation_id: int,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    folio = db.query(models.Folio).filter(models.Folio.reservation_id == reservation_id).first()
    if folio:
        return folio

    folio = models.Folio(reservation_id=reservation_id)
    db.add(folio)
    db.commit()
    db.refresh(folio)
    return folio

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
    folio_id: int,
    base_amount: float,
    description: str,
    charge_type: models.ChargeType,
    apply_taxes: bool = True,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")

    if apply_taxes:
        taxes = tax_logic.calculate_maldives_taxes(base_amount)
        charge = models.Charge(
            folio_id=folio_id,
            type=charge_type,
            amount=taxes["total_amount"],
            base_amount=base_amount,
            service_charge=taxes["service_charge"],
            tgst=taxes["tgst"],
            green_tax=taxes["green_tax"],
            description=description
        )
    else:
        charge = models.Charge(
            folio_id=folio_id,
            type=charge_type,
            amount=base_amount,
            base_amount=base_amount,
            description=description
        )

    db.add(charge)
    folio.total_amount += charge.amount
    db.add(folio)
    db.commit()
    db.refresh(charge)
    return charge

@router.post("/payments", response_model=schemas.Payment)
def post_payment(
    *,
    db: Session = Depends(deps.get_db),
    payment_in: schemas.PaymentCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    folio = db.query(models.Folio).filter(models.Folio.id == payment_in.folio_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")

    payment = models.Payment(**payment_in.dict())
    db.add(payment)

    folio.paid_amount += payment.amount
    if folio.paid_amount >= folio.total_amount:
        folio.status = models.PaymentStatus.PAID
    elif folio.paid_amount > 0:
        folio.status = models.PaymentStatus.PARTIAL

    db.add(folio)
    db.commit()
    db.refresh(payment)
    return payment
