from sqlalchemy.orm import Session
from united_transfer_system import models, schemas
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
            trace_id=f"LEG-{uuid.uuid4().hex[:8]}", # MANDATORY TRACE_ID
            type=leg_in.type,
            origin=leg_in.origin,
            destination=leg_in.destination,
            departure_time=leg_in.departure_time,
            master_voucher_code=f"QR-{uuid.uuid4().hex[:10].upper()}"
        )
        db.add(db_leg)

    db.flush()

    shadow_service.commit_evidence(db, obj_in.trace_id, {
        "actor": actor,
        "action": "CREATE_JOURNEY",
        "entity_id": db_journey.id,
        "legs_count": len(obj_in.legs)
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

def finalize_invoice(db: Session, journey_id: int, trace_id: str, actor: str):
    """
    Finalize the invoice for a completed journey.
    """
    journey = db.query(models.Journey).filter(models.Journey.id == journey_id).first()
    if not journey:
        raise ValueError("Journey not found")

    # Logic to calculate final amounts and generate invoice
    # In sandbox, we just update status and commit evidence
    journey.status = models.JourneyStatus.COMPLETED

    shadow_service.commit_evidence(db, trace_id, {
        "actor": actor,
        "action": "FINALIZE_INVOICE",
        "journey_id": journey_id,
        "status": "COMPLETED"
    })
    db.commit()
    return {"status": "finalized", "journey_id": journey_id}
