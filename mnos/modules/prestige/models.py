from typing import List, Optional, Dict
from pydantic import BaseModel

class TripMasterObject(BaseModel):
    trip_id: str
    status: str = "provisional"
    planner_id: str
    itinerary: List[Dict] = []
    pricing_breakdown: Dict = {}
    compliance_score: float = 0.0
    human_approved: bool = False
    shadow_proof: Optional[str] = None

class OutreachContact(BaseModel):
    contact_id: str
    full_name: str
    email: str
    priority: str  # A, B, C
    lead_score: int
    requires_approval: bool = False

    @classmethod
    def from_csv_row(cls, row: Dict):
        # FIX: Cast lead_score to integer before comparison to avoid crashes.
        try:
            l_score = int(row.get("lead_score", 0))
        except (ValueError, TypeError):
            l_score = 0

        priority = row.get("priority", "C")

        return cls(
            contact_id=row.get("contact_id", "UNKNOWN"),
            full_name=row.get("full_name", "Anonymous"),
            email=row.get("email", ""),
            priority=priority,
            lead_score=l_score,
            requires_approval=(priority == "A" or l_score >= 13)
        )
