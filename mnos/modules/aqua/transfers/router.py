from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mnos.core.api import deps
from mnos.modules.aqua.transfers import schemas, service, models

router = APIRouter()

@router.get("/vehicles", response_model=List[schemas.Vehicle])
def read_vehicles(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return db.query(models.Vehicle).offset(skip).limit(limit).all()

@router.post("/vehicles", response_model=schemas.Vehicle)
def create_vehicle(
    *,
    db: Session = Depends(deps.get_db),
    vehicle_in: schemas.VehicleCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return service.create_vehicle(db, vehicle_in=vehicle_in, actor=current_user.email)

@router.post("/", response_model=schemas.TransferRequest)
def create_transfer_request(
    *,
    db: Session = Depends(deps.get_db),
    request_in: schemas.TransferRequestCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return service.create_transfer_request(db, request_in=request_in, actor=current_user.email)

@router.get("/{request_id}", response_model=schemas.TransferRequest)
def read_transfer_request(
    request_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    db_obj = db.query(models.TransferRequest).filter(models.TransferRequest.id == request_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Transfer request not found")
    return db_obj
