from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import UUID

class RetailEvent(BaseModel):
    event_type: str
    tenant_id: UUID
    session_id: UUID
    trace_id: UUID
    payload: Dict[str, Any]

# Outbound Event Types
EVENT_SESSION_STARTED = "retail.session_started"
EVENT_CART_UPDATED = "retail.cart_updated"
EVENT_SESSION_EXITED = "retail.session_exited"
EVENT_SESSION_FLAGGED = "retail.session_flagged"
EVENT_SESSION_SETTLED = "retail.session_settled"
EVENT_SESSION_CANCELLED = "retail.session_cancelled"

# Inbound Event Types (for consumption)
EVENT_AEGIS_USER_SUSPENDED = "aegis.user_suspended"
EVENT_FCE_SETTLEMENT_FAILED = "fce.settlement_failed"
EVENT_GOVERNANCE_REVIEW_COMPLETED = "governance.review_completed"
