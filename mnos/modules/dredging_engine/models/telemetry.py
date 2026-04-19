from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class DragflowSensor(BaseModel):
    vibration: float
    temperature: float
    inclination: float
    data_source: str = "REAL" # REAL or SIMULATED

class SeafarerTelemetry(BaseModel):
    latitude: float
    longitude: float
    sedimentation_depth: float

class DredgepackData(BaseModel):
    precision_x: float
    precision_y: float
    z_depth: float

class BoatState(BaseModel):
    current_path: List[dict]
    fuel_level: float
    passenger_count: int
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class FullTelemetry(BaseModel):
    dragflow: DragflowSensor
    seafarer: SeafarerTelemetry
    dredgepack: DredgepackData
    boat_state: BoatState
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
