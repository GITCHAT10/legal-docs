from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import create_restaurant_order
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/v1/restaurant")

class OrderCreate(BaseModel):
    facility_id: str
    items: List[dict]
    total_amount: float
    tenant_id: str = "sf_maldives_001"

@router.post("/order")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    return create_restaurant_order(db, **order.model_dump())
