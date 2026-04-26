from sqlalchemy.orm import Session
from united_transfer_system import models, schemas
import uuid
import logging
from typing import Dict, Any, Optional
from mnos.core.events.dispatcher import event_dispatcher, CanonicalEvent

async def create_journey(db: Session, *, obj_in: schemas.JourneyCreate, ctx: Dict[str, Any]) -> models.Journey:
    # 1. Create Journey record
    db_journey = models.Journey(
        tenant_id=obj_in.tenant_id,
        trace_id=obj_in.trace_id,
        aegis_id=ctx.get("aegis_id"),
        device_id=ctx.get("device_id"),
        external_reference=obj_in.external_reference,
        status=models.JourneyStatus.CREATED
    )
    db.add(db_journey)
    db.flush()

    # 2. Create Leg records
    for leg_in in obj_in.legs:
        db_leg = models.Leg(
            journey_id=db_journey.id,
            trace_id=db_journey.trace_id,
            type=leg_in.type,
            origin=leg_in.origin,
            destination=leg_in.destination,
            departure_time=leg_in.departure_time,
            master_voucher_code=f"QR-{uuid.uuid4().hex[:10].upper()}"
        )
        db.add(db_leg)

    db.commit()
    db.refresh(db_journey)

    # Standardized Event Dispatching
    event_dispatcher.dispatch(
        CanonicalEvent.TRANSFER_PROVISIONED,
        {
            "journey_id": db_journey.id,
            "trace_id": str(db_journey.trace_id)
        },
        ctx={
            "trace_id": str(db_journey.trace_id),
            "aegis_id": ctx.get("aegis_id"),
            "device_id": ctx.get("device_id")
        }
    )

    return db_journey

def get_availability(db: Session, query: schemas.AvailabilityQuery):
    return [
        {"type": "land", "provider": "Taxi-01", "price": 150.0},
        {"type": "air", "provider": "IAS-ATR72", "price": 2500.0},
        {"type": "sea", "provider": "Speedboat-X", "price": 500.0}
    ]
