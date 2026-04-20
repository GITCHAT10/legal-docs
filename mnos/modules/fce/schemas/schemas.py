from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from mnos.modules.fce.models import FolioStatus, ChargeType
from decimal import Decimal

class ChargeBase(BaseModel):
    type: ChargeType
    total_amount: Decimal = Field(default=Decimal("0.0"), alias="amount")
    description: Optional[str] = None
    base_amount: Decimal
    service_charge: Decimal = Decimal("0.0")
    tgst: Decimal = Decimal("0.0")
    green_tax: Decimal = Decimal("0.0")
    model_config = ConfigDict(populate_by_name=True)

class ChargeCreate(ChargeBase):
    folio_id: int
    trace_id: str

class Charge(ChargeBase):
    id: int
    folio_id: int
    trace_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class PaymentCreate(BaseModel):
    folio_id: int
    amount: Decimal
    method: str
    trace_id: str
    transaction_reference: Optional[str] = None

class Payment(BaseModel):
    id: int
    folio_id: int
    trace_id: str
    amount: Decimal
    method: str
    transaction_reference: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FolioBase(BaseModel):
    external_reservation_id: str
    trace_id: str
    total_amount: Decimal = Decimal("0.0")
    paid_amount: Decimal = Decimal("0.0")
    status: FolioStatus = FolioStatus.OPEN

class Folio(FolioBase):
    id: int
    charges: List[Charge] = Field(default=[], alias="lines")
    payments: List[Payment] = []
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
