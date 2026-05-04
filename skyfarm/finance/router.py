from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import capture_payment, generate_invoice_data, create_payout_batch
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/finance")

class PaymentCreate(BaseModel):
    amount: float
    reference_id: str
    tenant_id: str = "sf_maldives_001"
    currency: str = "USD"

class InvoiceRequest(BaseModel):
    base_price: float
    reference_id: str

class PayoutRequest(BaseModel):
    amount: float
    tenant_id: str = "sf_maldives_001"

@router.post("/payment")
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    return capture_payment(db, **payment.model_dump())

@router.post("/invoice/generate")
def generate_invoice(req: InvoiceRequest):
    return generate_invoice_data(req.base_price, req.reference_id)

@router.post("/payout/create")
def create_payout(req: PayoutRequest, db: Session = Depends(get_db)):
    return create_payout_batch(db, req.amount, req.tenant_id)
