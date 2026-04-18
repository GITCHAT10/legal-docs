from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import log_fish_intake
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1")

class CatchCreate(BaseModel):
    vessel_id: str
    species: str
    weight: float
    location: str
    tenant_id: str = "sf_maldives_001"

@router.post("/marine/catch")
def create_catch(catch: CatchCreate, db: Session = Depends(get_db)):
    return log_fish_intake(db, **catch.model_dump())
