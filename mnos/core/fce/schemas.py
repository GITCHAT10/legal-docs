from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from .models import FolioStatus, ChargeType, TransactionStatus

class FolioBase(BaseModel):
    external_reservation_id: str
    trace_id: str
    tenant_id: str = "default"
    guest_id: Optional[int] = None

class FolioCreate(FolioBase):
    pass

class Folio(FolioBase):
    id: int
    status: FolioStatus
    total_amount: float
    paid_amount: float
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True

class FolioLineBase(BaseModel):
    type: ChargeType
    base_amount: float
    description: Optional[str] = None
    trace_id: str
    tenant_id: str = "default"
    apply_green_tax: bool = False
    nights: int = 0
    currency: str = "USD"

class FolioLineCreate(FolioLineBase):
    pass

class FolioLine(BaseModel):
    id: int
    folio_id: int
    type: ChargeType
    base_amount: float
    service_charge: float
    tgst: float
    green_tax: float
    amount: float
    currency: str
    exchange_rate: float
    description: Optional[str]
    is_reversed: bool
    created_at: datetime
    trace_id: str

    class Config:
        from_attributes = True

class FolioTransactionBase(BaseModel):
    amount: float
    method: str
    trace_id: str
    tenant_id: str = "default"
    currency: str = "USD"

class FolioTransaction(FolioTransactionBase):
    id: int
    folio_id: int
    status: TransactionStatus
    created_at: datetime

    class Config:
        from_attributes = True

class Invoice(BaseModel):
    id: int
    folio_id: int
    invoice_number: str
    total_amount: float
    currency: str
    tax_summary: Any
    created_at: datetime

    class Config:
        from_attributes = True
