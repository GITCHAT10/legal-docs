from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from .models import FolioStatus, ChargeType, TransactionStatus

class FolioBase(BaseModel):
    external_reservation_id: str
    trace_id: str
    tenant_id: str = "default"

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
    tax_summary: Optional[Any] = None
    status: str = "finalized"
    created_at: datetime

    class Config:
        from_attributes = True
