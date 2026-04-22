from sqlalchemy.orm import Session
from mnos.modules.united_transfer import models, schemas
from mnos.modules.shadow import service as shadow_service
import uuid

def create_journey(db: Session, *, obj_in: schemas.JourneyCreate, actor: str) -> models.Journey:
    db_journey = models.Journey(
        tenant_id=obj_in.tenant_id,
        trace_id=obj_in.trace_id,
        external_reference=obj_in.external_reference
    )
    db.add(db_journey)
    db.flush()

    for leg_in in obj_in.legs:
        db_leg = models.Leg(
            journey_id=db_journey.id,
            type=leg_in.type,
            origin=leg_in.origin,
            destination=leg_in.destination,
            departure_time=leg_in.departure_time,
            master_voucher_code=f"QR-{uuid.uuid4().hex[:10].upper()}"
        )
        db.add(db_leg)

    db.flush()

    # Use hardened SHADOW service
    from mnos.modules.shadow.service import shadow
    shadow.commit("CREATE_JOURNEY", {
        "actor": actor,
        "entity_id": db_journey.id,
        "legs_count": len(obj_in.legs),
        "trace_id": obj_in.trace_id
    })

    db.commit()
    db.refresh(db_journey)
    return db_journey

def get_availability(db: Session, query: schemas.AvailabilityQuery):
    # Stub for real-time availability across modes
    return [
        {"type": "land", "provider": "Taxi-01", "price": 150.0},
        {"type": "air", "provider": "IAS-ATR72", "price": 2500.0},
        {"type": "sea", "provider": "Speedboat-X", "price": 500.0}
    ]
