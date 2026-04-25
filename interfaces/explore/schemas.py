from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class EventBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    category: str
    start_at: datetime
    end_at: datetime
    venue_name: str
    island: str
    atoll: str

class EventLogistics(BaseModel):
    event_id: str
    transport_required: bool
    transport_mode: Optional[str] = None
    available_routes: List[str] = []
    recommended_departure_window: Optional[str] = None

class SpatialPulseSchema(BaseModel):
    event_id: str
    pulse_strength: float
    occupancy_hint: int
    vibe_score: float
    reachability_score: float
    boat_eta_hint: Optional[str] = None
