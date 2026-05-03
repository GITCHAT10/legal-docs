from pydantic import BaseModel
from typing import Optional, Dict, Any

class LeadCard(BaseModel):
    lead_id: str
    score: int
    tier: str
    priority: str
    source_platform: str
    campaign_id: str
    content_id: str
    guest_name: str
    guest_handle: str
    market: str
    country: str
    whatsapp_status: str
    ai_summary: Dict[str, Any]
    quote_panel: Optional[Dict[str, Any]] = None
    compliance_warnings: list[str] = []
