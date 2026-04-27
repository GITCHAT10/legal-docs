from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from decimal import Decimal

class PricingRequest(BaseModel):
    net_amount: Decimal = Field(..., gt=0)
    currency: str = Field(..., pattern="^(USD|EUR|MVR)$")
    product_type: str = Field(..., pattern="^(ACCOMMODATION|TRANSFER_SEA|TRANSFER_AIR|ACTIVITY|FNB|RETAIL|SERVICE|PACKAGE|FEE)$")
    trace_id: str
    tax_type: Optional[str] = "TOURISM_STANDARD"
    channel: Optional[str] = "DIRECT"
    agent_type: Optional[str] = "B2B"
    allotment_override_pct: Optional[Decimal] = None

class PricingResult(BaseModel):
    status: str
    total_mvr: float
    breakdown: Dict[str, Any]
    price_trace: Dict[str, Any]
