from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any
from decimal import Decimal

class SessionStartRequest(BaseModel):
    store_id: str
    auth_type: str
    auth_token: str

class SessionResponse(BaseModel):
    session_id: UUID
    status: str
    unlock: bool

class SensorEventRequest(BaseModel):
    session_id: UUID
    event_type: str
    source: str
    product_id: Optional[str] = None
    qty: Optional[Decimal] = None
    confidence: Decimal
    timestamp: datetime

class CartItemSchema(BaseModel):
    product_id: str
    qty: Decimal
    unit_price: Decimal
    subtotal: Decimal
    confidence_score: Decimal

class CartResponse(BaseModel):
    session_id: UUID
    items: List[CartItemSchema]
    running_total: Decimal

class SessionExitRequest(BaseModel):
    session_id: UUID

class FCESettleRequest(BaseModel):
    tenant_id: UUID
    aegis_user_id: UUID
    session_id: UUID
    trace_id: UUID
    source_module: str = "A_RETAIL"
    items: List[dict]
    base_amount: Decimal
    fee_profile: str = "AUTONOMOUS_RETAIL_STANDARD"

class FCESettleResponse(BaseModel):
    status: str
    receipt_id: str
    settlement_id: UUID
    breakdown: dict

class ShadowCommitRequest(BaseModel):
    tenant_id: UUID
    trace_id: UUID
    entity_type: str = "A_RETAIL_SESSION"
    entity_id: UUID
    event_type: str
    payload: dict
