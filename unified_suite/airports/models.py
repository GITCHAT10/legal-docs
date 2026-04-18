from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Flight(BaseModel):
    flight_number: str
    airline: str
    origin: str
    destination: str
    arrival_time: datetime
    departure_time: Optional[datetime] = None
    gate: Optional[str] = None
    status: str = "SCHEDULED" # SCHEDULED, ARRIVED, DEPARTED, CANCELLED

class AirportTerminalStatus(BaseModel):
    terminal_id: str
    active_gates: List[str]
    active_flights: List[Flight]
