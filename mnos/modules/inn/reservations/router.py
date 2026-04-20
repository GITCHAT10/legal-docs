from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mnos.core.api import deps
from mnos.modules.inn.reservations import schemas, service, models

router = APIRouter()

@router.post("/", response_model=schemas.Reservation)
def create_reservation(
    *,
    db: Session = Depends(deps.get_db),
    reservation_in: schemas.ReservationCreate,
    current_user: service.models.Base = Depends(deps.get_current_user),
) -> Any:
    """
    Create new reservation.
    """
    return service.create_reservation(db, reservation_in=reservation_in)

@router.get("/{reservation_id}", response_model=schemas.Reservation)
def read_reservation(
    reservation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: service.models.Base = Depends(deps.get_current_user),
) -> Any:
    """
    Get reservation by ID.
    """
    reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation

@router.patch("/{reservation_id}/status", response_model=schemas.Reservation)
def update_reservation_status(
    reservation_id: int,
    status_in: schemas.ReservationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: service.models.Base = Depends(deps.get_current_user),
) -> Any:
    """
    Update reservation status.
    """
    reservation = service.update_reservation_status(db, reservation_id=reservation_id, status=status_in.status)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation

@router.post("/rooms", response_model=schemas.Room)
def create_room(
    *,
    db: Session = Depends(deps.get_db),
    room_in: schemas.RoomCreate,
    current_user: service.models.Base = Depends(deps.get_current_user),
) -> Any:
    """
    Create new room.
    """
    db_room = models.Room(**room_in.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@router.get("/rooms/", response_model=List[schemas.Room])
def read_rooms(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: service.models.Base = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve rooms.
    """
    rooms = db.query(models.Room).offset(skip).limit(limit).all()
    return rooms
from typing import Any
