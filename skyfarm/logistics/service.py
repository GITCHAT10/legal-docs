from sqlalchemy.orm import Session
from .models import LogisticsEventModel
import uuid

def record_logistics_event(db: Session, batch_id: str, status: str, origin: str, destination: str, vessel_id: str = None):
    event = LogisticsEventModel(
        id=f"log_{uuid.uuid4().hex[:8]}",
        batch_id=batch_id,
        vessel_id=vessel_id,
        origin=origin,
        destination=destination,
        status=status
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
