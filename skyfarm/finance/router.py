from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import capture_payment, record_item_sold
from pydantic import BaseModel

router = APIRouter()

class PaymentCreate(BaseModel):
    amount: float
    reference_id: str
    currency: str = "USD"

@router.post("/finance/payment")
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    return capture_payment(db, **payment.dict())

@router.post("/retail/sale")
def create_sale(sale: PaymentCreate, db: Session = Depends(get_db)):
    return record_item_sold(db, sale.amount, sale.reference_id)
