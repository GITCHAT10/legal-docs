from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, time

class UHNWBookingTemplate(BaseModel):
    # Core Lead
    lead_type: str
    main_contact: str
    travel_dates: Dict[str, date] # from, to

    # Pax
    adults: int = Field(..., gt=0)
    children: int = 0
    infants: int = 0
    staff: int = 0
    security: int = 0
    nationalities: List[str]

    # Arrival
    arrival_mode: str # SCHEDULED, PRIVATE_JET, YACHT
    flight_no: Optional[str] = None
    private_jet_tail_no: Optional[str] = None
    origin_airport: Optional[str] = None
    eta: Optional[time] = None
    fbo_or_terminal: Optional[str] = None
    luggage_details: Dict[str, Any]

    # Preferences
    villa_preference: List[str]
    privacy_level: str # P1, P2, P3, P4
    security_detail_required: bool = False
    dietary_rules: List[str] = []
    medical_needs: Optional[str] = None
    celebration_event: Optional[str] = None
    transfer_preference: str
    resort_style: List[str] = []

    # Commercial
    budget_band: str
    payment_preference: str
    agent_terms: Optional[str] = None
    must_avoid_notes: Optional[str] = None
