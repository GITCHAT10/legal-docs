from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import record_logistics_event
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/logistics")

class LogisticsCreate(BaseModel):
    batch_id: str
    status: str
    origin: str
    destination: str
    tenant_id: str = "sf_maldives_001"
    temperature_c: float = 2.0
    vessel_id: Optional[str] = None

@router.post("/event")
def create_logistics_event(event: LogisticsCreate, db: Session = Depends(get_db)):
    return record_logistics_event(db, **event.model_dump())
