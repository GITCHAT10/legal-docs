from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import log_farm_harvest, create_farm_batch
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/v1")

class HarvestCreate(BaseModel):
    facility_id: str
    crop_type: str
    quantity: float
    unit: str
    tenant_id: str = "sf_maldives_001"

class BatchCreate(BaseModel):
    source_ids: List[str]
    tenant_id: str = "sf_maldives_001"

@router.post("/agri/harvest")
def create_harvest(harvest: HarvestCreate, db: Session = Depends(get_db)):
    return log_farm_harvest(db, **harvest.model_dump())

@router.post("/production/batch")
def create_batch(batch: BatchCreate, db: Session = Depends(get_db)):
    return create_farm_batch(db, batch.source_ids, batch.tenant_id)
