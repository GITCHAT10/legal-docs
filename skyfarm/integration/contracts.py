from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

class SuccessResponse(BaseModel):
    success: bool = True
    request_id: str
    data: Dict[str, Any] = {}
    error: Optional[Any] = None
    meta: Dict[str, Any] = Field(default_factory=lambda: {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "v1"
    })

class FailureError(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = {}

class FailureResponse(BaseModel):
    success: bool = False
    request_id: str
    data: Optional[Any] = None
    error: FailureError
    meta: Dict[str, Any] = Field(default_factory=lambda: {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "v1"
    })

class EventEnvelope(BaseModel):
    event_id: str
    event_type: str
    event_version: str = "1.0"
    occurred_at: str
    producer: str = "skyfarm"
    payload: Dict[str, Any]
    audit: Optional[Dict[str, Any]] = None
