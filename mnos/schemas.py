from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime

class EventPayloadSchema(BaseModel):
    event_id: str
    source: str = "skyfarm"
    tenant_id: str
    type: str
    timestamp: str
    data: Dict[str, Any]

class SuccessResponse(BaseModel):
    success: bool = True
    request_id: str
    data: Dict[str, Any]

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    request_id: str
    error: ErrorDetail
