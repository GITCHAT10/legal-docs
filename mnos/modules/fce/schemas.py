from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel
from mnos.modules.fce.models import FolioStatus, PaymentStatus, ChargeType

class FolioLineBase(BaseModel):
    trace_id: str
    type: ChargeType
    base_amount: float
    description: Optional[str] = None

class FolioLineCreate(FolioLineBase):
    apply_green_tax: bool = False
    nights: int = 0

class FolioLine(FolioLineBase):
    id: int
    folio_id: int
    service_charge: float
    tgst: float
    green_tax: float
    amount: float
    is_reversed: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    trace_id: str
    amount: float
    method: str
    status: PaymentStatus = PaymentStatus.PAID

class PaymentCreate(PaymentBase):
    folio_id: int

class Payment(PaymentBase):
    id: int
    folio_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Invoice(BaseModel):
    id: int
    folio_id: int
    invoice_number: str
    total_amount: float
    tax_summary: Dict[str, float]
    created_at: datetime

    class Config:
        from_attributes = True

class FolioBase(BaseModel):
    external_reservation_id: str
    trace_id: str
    currency: str = "USD"

class FolioCreate(FolioBase):
    pass

class Folio(FolioBase):
    id: int
    status: FolioStatus
    total_amount: float
    paid_amount: float
    created_at: datetime
    lines: List[FolioLine] = []
    payments: List[Payment] = []

    class Config:
        from_attributes = True
