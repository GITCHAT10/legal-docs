from sqlalchemy.orm import Session
from mnos.modules.ut_safari.models import vessel as models
from typing import Dict, Any

def register_vessel(db: Session, data: Dict[str, Any]) -> models.Vessel:
    vessel = models.Vessel(**data)
    db.add(vessel)
    db.commit()
    db.refresh(vessel)
    return vessel

def get_active_safaris(db: Session):
    return db.query(models.Vessel).filter(models.Vessel.type == models.VesselType.SAFARI, models.Vessel.is_active == True).all()
