from pydantic import BaseModel
from typing import Optional, Any, Dict
import uuid

class MnosResponse(BaseModel):
    transaction_id: str
    event_id: Optional[str] = None
    shadow_id: Optional[str] = None
    policy_decision_id: Optional[str] = None
    status: str
    data: Optional[Any] = None
    message: Optional[str] = None

class MnosEnvelope(BaseModel):
    mnos: str = "1.0"
    module: str
    transaction_id: str
    shadow_id: Optional[str] = None
    event_id: Optional[str] = None
    policy_decision_id: Optional[str] = None
    status: str
    data: Optional[Any] = None

class ShadowEnvelope(BaseModel):
    shadow_id: str
    event_id: str
    decision: str
    result: str
    audit_hash: str
    data: Optional[Any] = None
