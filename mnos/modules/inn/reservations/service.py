from typing import List, Optional, Any
from sqlalchemy.orm import Session
from mnos.modules.inn.reservations import models, schemas
from mnos.core.events.dispatcher import event_dispatcher, CanonicalEvent
from mnos.modules.shadow import service as shadow_service
import uuid
from datetime import date

def create_reservation(db: Session, *, reservation_in: schemas.ReservationCreate, actor: str = "SYSTEM") -> models.Reservation:
    try:
        if not reservation_in.trace_id: raise ValueError("trace_id required")

        # Validate capacity
        for stay_in in reservation_in.stays:
            room = db.query(models.Room).filter(models.Room.id == stay_in.room_id).first()
            if room and (reservation_in.adults + reservation_in.children) > room.capacity:
                raise ValueError(f"Room {room.room_number} capacity exceeded")

        # 1. Create Reservation record
        db_reservation = models.Reservation(
            tenant_id=reservation_in.tenant_id,
            trace_id=reservation_in.trace_id,
            guest_id=reservation_in.guest_id,
            status=reservation_in.status,
            total_amount=reservation_in.total_amount,
            adults=reservation_in.adults,
            children=reservation_in.children,
            created_by=actor
        )
        db.add(db_reservation)
        db.flush()

        # 2. Create Stay records
        for stay_in in reservation_in.stays:
            db_stay = models.Stay(
                tenant_id=reservation_in.tenant_id,
                trace_id=f"STAY-{uuid.uuid4().hex[:8]}",
                reservation_id=db_reservation.id,
                room_id=stay_in.room_id,
                check_in_date=stay_in.check_in_date,
                check_out_date=stay_in.check_out_date,
                created_by=actor
            )
            db.add(db_stay)

        db.flush()

        shadow_service.commit_evidence(db, reservation_in.trace_id, {
            "actor": actor, "action": "CREATE_RESERVATION", "entity_type": "RESERVATION", "entity_id": db_reservation.id,
            "after_state": {"guest_id": db_reservation.guest_id, "status": db_reservation.status}
        })

        db.commit()
        db.refresh(db_reservation)

        # Standardized Event Dispatching
        event_dispatcher.dispatch(CanonicalEvent.RESERVATION_CONFIRMED, {
            "reservation_id": db_reservation.id,
            "guest_id": db_reservation.guest_id
        }, ctx={"trace_id": db_reservation.trace_id, "aegis_id": actor})

        return db_reservation
    except Exception:
        db.rollback()
        raise

def change_room(db: Session, reservation_id: int, old_room_id: int, new_room_id: int, actor: str = "SYSTEM") -> models.Stay:
    try:
        res = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
        if not res: raise ValueError("Reservation not found")

        trace_id = f"ROOM-CHANGE-{uuid.uuid4().hex[:8]}"

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
            tenant_id=res.tenant_id,
            trace_id=f"STAY-{uuid.uuid4().hex[:8]}",
            reservation_id=reservation_id,
            room_id=new_room_id,
            check_in_date=date.today(),
            check_out_date=old_stay.check_out_date if old_stay else date.today(),
            is_active=True,
            created_by=actor
        )
        db.add(new_stay)

        # 3. Update room statuses
        update_room_status(db, old_room_id, models.RoomStatus.DIRTY, actor)
        update_room_status(db, new_room_id, models.RoomStatus.OCCUPIED, actor)

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

def update_reservation_status(db: Session, reservation_id: int, status: models.ReservationStatus, actor: str = "SYSTEM") -> Optional[models.Reservation]:
    try:
        db_reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
        if not db_reservation: return None

        trace_id = f"RES-STATUS-{uuid.uuid4().hex[:8]}"
        before_state = {"status": db_reservation.status}

        db_reservation.status = status

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

def create_room(db: Session, *, room_in: schemas.RoomCreate, actor: str = "SYSTEM") -> models.Room:
    try:
        db_room = models.Room(
            tenant_id=room_in.tenant_id,
            trace_id=room_in.trace_id,
            room_number=room_in.room_number,
            room_type=room_in.room_type,
            status=room_in.status,
            base_price=room_in.base_price,
            capacity=room_in.capacity,
            created_by=actor
        )
        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        return db_room
    except Exception:
        db.rollback()
        raise
