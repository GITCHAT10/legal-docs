from enum import Enum
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class BriefType(str, Enum):
    PROPOSAL = "PROPOSAL"
    AGENT_FINAL = "AGENT_FINAL"
    GUEST_FINAL = "GUEST_FINAL"

class PrestigeBrief(BaseModel):
    brief_id: str
    brief_type: BriefType
    guest_name: str
    itinerary: List[Dict[str, Any]]
    transfer_logistics: List[Dict[str, Any]]
    villa_summary: Dict[str, Any]
    pricing_items: List[Dict[str, Any]]
    payment_status: str
    emergency_contacts: List[Dict[str, str]]
    shadow_proof_status: str
