from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from mnos.modules.fce.models import PaymentStatus, ChargeType, FolioStatus

class ChargeBase(BaseModel):
    type: ChargeType
    amount: float
    description: Optional[str] = None
    base_amount: float
    service_charge: float = 0.0
    tgst: float = 0.0
    green_tax: float = 0.0

class ChargeCreate(ChargeBase):
    folio_id: int

class Charge(ChargeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    folio_id: int
    amount: float
    method: str
    transaction_reference: Optional[str] = None

class Payment(BaseModel):
    id: int
    folio_id: int
    amount: float
    method: str
    transaction_reference: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FolioBase(BaseModel):
    external_reservation_id: str
    total_amount: float = 0.0
    paid_amount: float = 0.0
    status: FolioStatus = FolioStatus.OPEN

class Folio(FolioBase):
    id: int
    charges: List[Charge] = []
    payments: List[Payment] = []

    class Config:
        from_attributes = True
