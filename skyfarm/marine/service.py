from sqlalchemy.orm import Session
from .models import CatchLogModel
from skyfarm.integration.outbox_service import queue_event
import uuid

def log_fish_intake(db: Session, vessel_id: str, species: str, weight: float, location: str, tenant_id: str):
    catch = CatchLogModel(
        id=f"fish_{uuid.uuid4().hex[:8]}",
        vessel_id=vessel_id,
        species=species,
        weight=weight,
        location=location,
        status="fish.intake.recorded"
    )
    db.add(catch)

    # Queue event for MNOS
    queue_event(db, tenant_id, "fish.intake.recorded", {
        "species": species,
        "gross_weight_kg": weight,
        "vessel_id": vessel_id,
        "landing_location": location
    })

    db.commit()
    db.refresh(catch)
    return catch
