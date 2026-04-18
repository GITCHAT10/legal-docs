from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from skyfarm.agri.service import log_harvest_completed, create_production_batch
from skyfarm.marine.service import log_fish_caught
from pydantic import BaseModel
from typing import List

router = APIRouter()

class CatchCreate(BaseModel):
    vessel_id: str
    species: str
    weight: float
    location: str

class HarvestCreate(BaseModel):
    facility_id: str
    crop_type: str
    quantity: float
    unit: str

class BatchCreate(BaseModel):
    source_ids: List[str]

@router.post("/marine/catch")
def create_catch(catch: CatchCreate, db: Session = Depends(get_db)):
    return log_fish_caught(db, **catch.dict())

@router.post("/agri/harvest")
def create_harvest(harvest: HarvestCreate, db: Session = Depends(get_db)):
    return log_harvest_completed(db, **harvest.dict())

@router.post("/production/batch")
def create_batch(batch: BatchCreate, db: Session = Depends(get_db)):
    return create_production_batch(db, batch.source_ids)
