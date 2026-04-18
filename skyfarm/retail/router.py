from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import record_retail_sale
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/v1/retail")

class SaleCreate(BaseModel):
    store_id: str
    items: List[dict]
    total_amount: float
    tenant_id: str = "sf_maldives_001"

@router.post("/sale")
def create_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    return record_retail_sale(db, **sale.model_dump())
