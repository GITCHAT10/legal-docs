from pydantic import BaseModel
from typing import List, Optional

class ClearanceResponse(BaseModel):
    status: str
    code: int
    clearance_token: Optional[str] = None
    integrity_status: str
    risk_score: float
    next_action: str
    reasons: Optional[List[str]] = None
    aegis_action: Optional[str] = None

class GenericResponse(BaseModel):
    status: str
    message: str
    shadow_id: Optional[str] = None
