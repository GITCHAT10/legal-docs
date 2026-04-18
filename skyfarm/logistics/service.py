from sqlalchemy.orm import Session
from .models import LogisticsEventModel
from skyfarm.integration.outbox_service import queue_event
from fastapi import HTTPException
import uuid

def record_logistics_event(db: Session, batch_id: str, status: str, origin: str, destination: str, tenant_id: str, temperature_c: float = 2.0, vessel_id: str = None):
    # Cold Chain Validation
    if temperature_c > 4.0:
        # Trigger Breach Event
        queue_event(db, tenant_id, "coldchain.breach.detected", {
            "batch_id": batch_id,
            "temperature_c": temperature_c,
            "location": origin
        })
        # Note: We still record the event but with breach flag if needed or just error

    event = LogisticsEventModel(
        id=f"log_{uuid.uuid4().hex[:8]}",
        batch_id=batch_id,
        vessel_id=vessel_id,
        origin=origin,
        destination=destination,
        status=status,
        metadata_json={"temperature_c": temperature_c}
    )
    db.add(event)

    # Generic logistics event sync
    queue_event(db, tenant_id, f"logistics.{status.lower()}", {
        "batch_id": batch_id,
        "origin": origin,
        "destination": destination
    })

    db.commit()
    db.refresh(event)
    return event
