from sqlalchemy.orm import Session
from .models import CatchLogModel
import uuid

def log_fish_caught(db: Session, vessel_id: str, species: str, weight: float, location: str):
    catch = CatchLogModel(
        id=f"fish_{uuid.uuid4().hex[:8]}",
        vessel_id=vessel_id,
        species=species,
        weight=weight,
        location=location,
        status="FISH_CAUGHT"
    )
    db.add(catch)
    db.commit()
    db.refresh(catch)
    return catch
