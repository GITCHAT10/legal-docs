from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class PredictiveDispatchPayload(BaseModel):
    event_id: str
    route_id: str
    departure_window: str
    dispatch_type: str = "PRE-HOLD"
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    trace_id: str

class BiometricVerifyPayload(BaseModel):
    subject_id: str
    gate_id: str
    verification_mode: str = "FACIAL"
    device_id: str
    wallet_fallback_id: Optional[str] = None
    trace_id: str

class GateDecision(BaseModel):
    decision: str  # PERMIT, DENY, FALLBACK
    reason: Optional[str] = None
    confidence_score: float
    trace_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
