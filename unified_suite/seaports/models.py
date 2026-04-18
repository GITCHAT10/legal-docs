from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Container(BaseModel):
    container_id: str
    size: int # 20 or 40 feet
    contents: str
    weight: float
    status: str = "IN_TRANSIT" # IN_TRANSIT, ARRIVED, CLEARED, DISPATCHED

class Vessel(BaseModel):
    vessel_id: str
    name: str
    origin: str
    arrival_time: datetime
    berth: Optional[str] = None
    containers: List[Container] = []
    status: str = "SCHEDULED" # SCHEDULED, DOCKED, DEPARTED
