from pydantic import BaseModel
from typing import List, Optional

class DragflowSensor(BaseModel):
    vibration: float
    temperature: float
    inclination: float

class SeafarerTelemetry(BaseModel):
    latitude: float
    longitude: float
    sedimentation_depth: float

class DredgepackData(BaseModel):
    precision_x: float
    precision_y: float
    z_depth: float

class BoatState(BaseModel):
    current_path: List[dict] # List of waypoint dicts
    fuel_level: float
    passenger_count: int

class FullTelemetry(BaseModel):
    dragflow: DragflowSensor
    seafarer: SeafarerTelemetry
    dredgepack: DredgepackData
    boat_state: BoatState
