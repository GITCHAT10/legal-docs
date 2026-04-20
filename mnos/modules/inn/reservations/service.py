from typing import List, Optional, Any
from sqlalchemy.orm import Session
from mnos.modules.inn.reservations import models, schemas
from mnos.core.events.dispatcher import event_dispatcher
from mnos.modules.shadow import service as shadow_service
import uuid
from datetime import date

def create_reservation(db: Session, *, reservation_in: schemas.ReservationCreate, actor: str = "SYSTEM") -> models.Reservation:
    try:
        trace_id = f"RES-{uuid.uuid4().hex[:8]}"

        # Validate capacity
        for stay_in in reservation_in.stays:
            room = db.query(models.Room).filter(models.Room.id == stay_in.room_id).first()
            if room and (reservation_in.adults + reservation_in.children) > room.capacity:
                raise ValueError(f"Room {room.room_number} capacity exceeded")

        # 1. Create Reservation record
        db_reservation = models.Reservation(
            guest_id=reservation_in.guest_id,
            status=reservation_in.status,
            total_amount=reservation_in.total_amount,
            adults=getattr(reservation_in, "adults", 1),
            children=getattr(reservation_in, "children", 0)
        )
        db.add(db_reservation)
        db.flush()

        # 2. Create Stay records
        for stay_in in reservation_in.stays:
            db_stay = models.Stay(
                reservation_id=db_reservation.id,
                room_id=stay_in.room_id,
                check_in_date=stay_in.check_in_date,
                check_out_date=stay_in.check_out_date
            )
            db.add(db_stay)

        db.flush()

        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor, "action": "CREATE_RESERVATION", "entity_type": "RESERVATION", "entity_id": db_reservation.id,
            "after_state": {"guest_id": db_reservation.guest_id, "status": db_reservation.status}
        })

        db.commit()
        db.refresh(db_reservation)
        event_dispatcher.dispatch("reservation_created", {"reservation_id": db_reservation.id})
        return db_reservation
    except Exception:
        db.rollback()
        raise

def change_room(db: Session, reservation_id: int, old_room_id: int, new_room_id: int, actor: str = "SYSTEM") -> models.Stay:
    try:
        res = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
        if not res: raise ValueError("Reservation not found")

        # 1. Close old stay
        old_stay = db.query(models.Stay).filter(
            models.Stay.reservation_id == reservation_id,
            models.Stay.room_id == old_room_id,
            models.Stay.is_active == True
        ).first()

        if old_stay:
            old_stay.is_active = False
            old_stay.check_out_date = date.today()

        # 2. Create new stay
        new_stay = models.Stay(
            reservation_id=reservation_id,
            room_id=new_room_id,
            check_in_date=date.today(),
            check_out_date=old_stay.check_out_date if old_stay else date.today(), # Placeholder
            is_active=True
        )
        db.add(new_stay)

        # 3. Update room statuses
        update_room_status(db, old_room_id, models.RoomStatus.DIRTY, actor)
        update_room_status(db, new_room_id, models.RoomStatus.OCCUPIED, actor)

        trace_id = f"ROOM-CHANGE-{uuid.uuid4().hex[:8]}"
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor, "action": "ROOM_CHANGE", "entity_type": "RESERVATION", "entity_id": reservation_id,
            "before_state": {"room_id": old_room_id},
            "after_state": {"room_id": new_room_id}
        })

        db.commit()
        return new_stay
    except Exception:
        db.rollback()
        raise

def handle_no_show(db: Session, reservation_id: int, actor: str = "SYSTEM"):
    return update_reservation_status(db, reservation_id, models.ReservationStatus.NO_SHOW, actor)

def update_reservation_status(db: Session, reservation_id: int, status: models.ReservationStatus, actor: str = "SYSTEM") -> Optional[models.Reservation]:
    try:
        db_reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
        if not db_reservation: return None

        trace_id = f"RES-STATUS-{uuid.uuid4().hex[:8]}"
        before_state = {"status": db_reservation.status}

        old_status = db_reservation.status
        db_reservation.status = status

        # If cancelled or no-show, auto-cancel transfers
        if status in [models.ReservationStatus.CANCELLED, models.ReservationStatus.NO_SHOW]:
            from mnos.modules.aqua.transfers.service import handle_reservation_cancellation
            handle_reservation_cancellation(db, reservation_id, actor)

        db.flush()
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor, "action": "UPDATE_RESERVATION_STATUS", "entity_type": "RESERVATION", "entity_id": db_reservation.id,
            "before_state": before_state, "after_state": {"status": status}
        })

        db.commit()
        db.refresh(db_reservation)
        return db_reservation
    except Exception:
        db.rollback()
        raise

def update_room_status(db: Session, room_id: int, status: models.RoomStatus, actor: str = "SYSTEM") -> Optional[models.Room]:
    try:
        db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
        if not db_room: return None
        trace_id = f"ROOM-STATUS-{uuid.uuid4().hex[:8]}"
        before_state = {"status": db_room.status}
        db_room.status = status
        db.flush()
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor, "action": "UPDATE_ROOM_STATUS", "entity_type": "ROOM", "entity_id": db_room.id,
            "before_state": before_state, "after_state": {"status": status}
        })
        db.commit()
        db.refresh(db_room)
        return db_room
    except Exception:
        db.rollback()
        raise

def create_room(db: Session, *, room_in: schemas.RoomCreate) -> models.Room:
    try:
        db_room = models.Room(**room_in.dict())
        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        return db_room
    except Exception:
        db.rollback()
        raise

def mark_room_ready_from_housekeeping(db: Session, room_id: int):
    return update_room_status(db, room_id, models.RoomStatus.READY)
