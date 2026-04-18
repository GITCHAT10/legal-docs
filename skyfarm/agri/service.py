from sqlalchemy.orm import Session
from .models import AgriHarvestModel, ProductionBatchModel
import uuid

def log_harvest_completed(db: Session, facility_id: str, crop_type: str, quantity: float, unit: str):
    harvest = AgriHarvestModel(
        id=f"agri_{uuid.uuid4().hex[:8]}",
        facility_id=facility_id,
        crop_type=crop_type,
        quantity=quantity,
        unit=unit
    )
    db.add(harvest)
    db.commit()
    db.refresh(harvest)
    return harvest

def create_production_batch(db: Session, source_ids: list):
    batch = ProductionBatchModel(
        id=f"batch_{uuid.uuid4().hex[:8]}",
        source_ids=source_ids,
        status="BATCH_CREATED"
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch
