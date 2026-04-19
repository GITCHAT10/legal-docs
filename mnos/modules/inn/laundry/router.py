from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mnos.core.api import deps
from mnos.modules.inn.laundry import schemas, models

router = APIRouter()

@router.post("/", response_model=schemas.LaundryItem)
def create_laundry_job(
    *,
    db: Session = Depends(deps.get_db),
    laundry_in: schemas.LaundryItemCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    db_obj = models.LaundryItem(**laundry_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=List[schemas.LaundryItem])
def read_laundry_jobs(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return db.query(models.LaundryItem).offset(skip).limit(limit).all()

@router.patch("/{laundry_id}", response_model=schemas.LaundryItem)
def update_laundry_job(
    laundry_id: int,
    update_in: schemas.LaundryItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    db_obj = db.query(models.LaundryItem).filter(models.LaundryItem.id == laundry_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Laundry job not found")

    if update_in.status:
        db_obj.status = update_in.status
    if update_in.total_price:
        db_obj.total_price = update_in.total_price

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
from typing import Any
