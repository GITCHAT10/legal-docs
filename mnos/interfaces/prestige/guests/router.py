from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mnos.core.api import deps
from mnos.interfaces.prestige.guests import models, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.Guest])
def read_guests(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve guests.
    """
    guests = db.query(models.Guest).offset(skip).limit(limit).all()
    return guests

@router.post("/", response_model=schemas.Guest)
def create_guest(
    *,
    db: Session = Depends(deps.get_db),
    guest_in: schemas.GuestCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Create new guest.
    """
    guest = db.query(models.Guest).filter(models.Guest.email == guest_in.email).first()
    if guest:
        raise HTTPException(
            status_code=400,
            detail="A guest with this email already exists.",
        )
    import uuid
    trace_id = f"GUEST-CREATE-{uuid.uuid4().hex[:8]}"
    guest = models.Guest(**guest_in.dict(), trace_id=trace_id)
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest

@router.get("/{guest_id}", response_model=schemas.Guest)
def read_guest_by_id(
    guest_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Get guest by ID.
    """
    guest = db.query(models.Guest).filter(models.Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest
