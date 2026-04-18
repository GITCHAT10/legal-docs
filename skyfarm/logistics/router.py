from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import record_logistics_event
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class LogisticsCreate(BaseModel):
    batch_id: str
    status: str
    origin: str
    destination: str
    vessel_id: Optional[str] = None

@router.post("/logistics/event")
def create_logistics_event(event: LogisticsCreate, db: Session = Depends(get_db)):
    return record_logistics_event(db, **event.dict())
