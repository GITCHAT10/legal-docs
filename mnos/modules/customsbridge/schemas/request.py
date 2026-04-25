from pydantic import BaseModel, Field
from typing import List, Optional

class ClearanceRequest(BaseModel):
    request_id: str
    container_id: str
    declaration_type: str
    commodity: str
    origin_site_id: Optional[str] = None
    mnos_batch_ids: List[str]
    declared_weight: float
    destination_country: Optional[str] = None
    requested_by_officer_id: str

class OverrideRequest(BaseModel):
    review_id: str
    officer_id: str
    reason: str
    scope: str = "THIS_REQUEST_ONLY"
    supervisor_id: str # Required for dual authorization

class InspectionResult(BaseModel):
    request_id: str
    inspection_result: str
    notes: Optional[str] = None
    officer_id: str
