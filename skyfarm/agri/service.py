from sqlalchemy.orm import Session
from .models import AgriHarvestModel, ProductionBatchModel
from skyfarm.integration.outbox_service import queue_event
from fastapi import HTTPException
import uuid

# Batch Lifecycle States: created, growing, harvested, quarantined

def log_farm_harvest(db: Session, facility_id: str, crop_type: str, quantity: float, unit: str, tenant_id: str):
    harvest = AgriHarvestModel(
        id=f"agri_{uuid.uuid4().hex[:8]}",
        facility_id=facility_id,
        crop_type=crop_type,
        quantity=quantity,
        unit=unit
    )
    db.add(harvest)

    # Queue event for MNOS
    queue_event(db, tenant_id, "farm.batch.harvested", {
        "facility_id": facility_id,
        "crop_type": crop_type,
        "quantity": quantity,
        "unit": unit
    })

    db.commit()
    db.refresh(harvest)
    return harvest

def create_farm_batch(db: Session, source_ids: list, tenant_id: str):
    batch = ProductionBatchModel(
        id=f"batch_{uuid.uuid4().hex[:8]}",
        source_ids=source_ids,
        status="created"
    )
    db.add(batch)

    # Queue event for MNOS
    queue_event(db, tenant_id, "farm.batch.created", {
        "batch_id": batch.id,
        "source_ids": source_ids
    })

    db.commit()
    db.refresh(batch)
    return batch

def update_batch_lifecycle(db: Session, batch_id: str, new_status: str, tenant_id: str):
    batch = db.query(ProductionBatchModel).filter(ProductionBatchModel.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    valid_states = ["created", "growing", "harvested", "quarantined"]
    if new_status not in valid_states:
        raise HTTPException(status_code=400, detail=f"Invalid batch status: {new_status}")

    batch.status = new_status

    queue_event(db, tenant_id, "farm.batch.lifecycle_updated", {
        "batch_id": batch_id,
        "status": new_status
    })

    db.commit()
    db.refresh(batch)
    return batch
