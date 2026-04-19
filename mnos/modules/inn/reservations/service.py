from typing import List, Optional
from sqlalchemy.orm import Session
from mnos.modules.inn.reservations import models, schemas
from mnos.core.events.dispatcher import event_dispatcher

def create_reservation(db: Session, *, reservation_in: schemas.ReservationCreate) -> models.Reservation:
    # 1. Create Reservation record
    db_reservation = models.Reservation(
        guest_id=reservation_in.guest_id,
        status=reservation_in.status,
        total_amount=reservation_in.total_amount
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)

    # 2. Create Stay records and allocate rooms (simple allocation for now)
    for stay_in in reservation_in.stays:
        db_stay = models.Stay(
            reservation_id=db_reservation.id,
            room_id=stay_in.room_id,
            check_in_date=stay_in.check_in_date,
            check_out_date=stay_in.check_out_date
        )
        db.add(db_stay)

        # Update room status to OCCUPIED if the reservation is confirmed and starts today
        # For simplicity, we just mark it as occupied if stay is created for now, or keep it ready
        # Real logic would check dates.

    db.commit()
    db.refresh(db_reservation)

    # 3. Dispatch event
    event_dispatcher.dispatch("reservation_created", {"reservation_id": db_reservation.id})

    return db_reservation

def update_reservation_status(db: Session, reservation_id: int, status: models.ReservationStatus) -> Optional[models.Reservation]:
    db_reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if not db_reservation:
        return None

    old_status = db_reservation.status
    db_reservation.status = status
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)

    if status == models.ReservationStatus.CONFIRMED and old_status != models.ReservationStatus.CONFIRMED:
        event_dispatcher.dispatch("reservation_confirmed", {"reservation_id": db_reservation.id})

    return db_reservation

def update_room_status(db: Session, room_id: int, status: models.RoomStatus) -> Optional[models.Room]:
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not db_room:
        return None
    db_room.status = status
    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    if status == models.RoomStatus.READY:
        event_dispatcher.dispatch("room_ready", {"room_id": room_id, "room_number": db_room.room_number})

    return db_room

def mark_room_ready_from_housekeeping(db: Session, room_id: int):
    """
    Called when housekeeping is completed.
    """
    return update_room_status(db, room_id, models.RoomStatus.READY)
