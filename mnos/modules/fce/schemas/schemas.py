from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from mnos.modules.fce.models import FolioStatus, PaymentStatus

class FolioBase(BaseModel):
    external_reservation_id: str
    trace_id: str

class FolioCreate(FolioBase):
    pass

class Folio(FolioBase):
    id: int
    status: FolioStatus
    total_amount: Decimal
    paid_amount: Decimal

    class Config:
        from_attributes = True

class ChargeBase(BaseModel):
    folio_id: int
    type: str
    base_amount: Decimal
    apply_green_tax: bool = False
    nights: int = 1
    pax: int = 1
    description: Optional[str] = None
    trace_id: str

class ChargeCreate(ChargeBase):
    pass

class Charge(ChargeBase):
    id: int
    service_charge: Decimal
    tgst: Decimal
    green_tax: Decimal
    total_amount: Decimal

    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    folio_id: int
    amount: Decimal
    method: str
    trace_id: str

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: int
    status: PaymentStatus

    class Config:
        from_attributes = True
