from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class WaterLane(BaseModel):
    lane_id: str
    heading: int # 0-359
    status: str = "OPEN" # OPEN, CLOSED, OCCUPIED

class WaterZone(BaseModel):
    zone_id: str
    location_name: str
    lanes: List[WaterLane]

class LoadManifest(BaseModel):
    flight_id: str
    passenger_count: int
    total_passenger_weight: float
    total_baggage_weight: float
    mtow_limit: float = 5670.0 # Twin Otter DHC-6 standard kg

class WeatherStatus(BaseModel):
    location_id: str
    wind_speed_knots: float
    wind_direction: int
    visibility_meters: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SeaplaneFlight(BaseModel):
    flight_id: str
    aircraft_id: str
    origin: str
    destination: str
    scheduled_departure: datetime
    status: str = "SCHEDULED" # SCHEDULED, GUEST_READY, BOARDING, DEPARTED, ARRIVED
    manifest: Optional[LoadManifest] = None
