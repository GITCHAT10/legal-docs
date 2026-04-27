from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from decimal import Decimal

class PricingRequest(BaseModel):
    net_amount: Decimal = Field(..., gt=0)
    currency: str = Field(..., pattern="^(USD|EUR|MVR)$")
    category: str = Field(..., pattern="^(ACCOMMODATION|TRANSFER|EXCURSION|PACKAGE|DEFAULT)$")
    tax_context: Optional[str] = "TOURISM"
    channel: Optional[str] = "DIRECT"
    agent_type: Optional[str] = "AGENT_STANDARD"
    allotment_override_pct: Optional[Decimal] = None

class PricingResult(BaseModel):
    currency_orig: str
    net_orig: float
    fx_rate: float
    net_mvr: float
    gross_mvr: float
    agent_commission: float
    platform_fee: float
    fce_breakdown: Dict[str, Any]
    total_mvr: float
    price_trace: Dict[str, Any]
    status: str
