from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import capture_payment
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1")

class PaymentCreate(BaseModel):
    amount: float
    reference_id: str
    tenant_id: str = "sf_maldives_001"
    currency: str = "USD"

@router.post("/finance/payment")
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    return capture_payment(db, **payment.model_dump())
