from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import record_custody_transfer, record_digital_twin_created
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/trace")

class TransferCreate(BaseModel):
    item_id: str
    from_actor: str
    to_actor: str
    tenant_id: str = "sf_maldives_001"

class TwinCreate(BaseModel):
    item_id: str
    actor_id: str
    metadata: dict = {}
    tenant_id: str = "sf_maldives_001"

@router.post("/transfer")
def create_transfer(transfer: TransferCreate, db: Session = Depends(get_db)):
    return record_custody_transfer(db, **transfer.model_dump())

@router.post("/twin")
def create_twin(twin: TwinCreate, db: Session = Depends(get_db)):
    return record_digital_twin_created(db, **twin.model_dump())
