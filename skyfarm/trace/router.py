from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import update_trace
from pydantic import BaseModel

router = APIRouter()

class TraceCreate(BaseModel):
    item_id: str
    action: str
    actor_id: str
    metadata: dict = {}

@router.post("/trace/record")
def create_trace_record(trace: TraceCreate, db: Session = Depends(get_db)):
    return update_trace(db, **trace.dict())
