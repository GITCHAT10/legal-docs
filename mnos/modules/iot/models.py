from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class MarsProtocol(str, Enum):
    MATTER = "matter"
    MQTT = "mqtt"
    CUSTOM = "custom"

class MarsDeviceSchema(BaseModel):
    id: str
    name: str
    protocol: MarsProtocol
    manufacturer: str
    model: str
    location: str
    capabilities: List[str] # switch, light, sensor, etc.
    firmware_version: str
    aegis_identity_ref: str # Identity mapping to AEGIS

class MarsEntitySchema(BaseModel):
    id: str
    device_id: str
    entity_type: str
    name: str

class MarsStateSchema(BaseModel):
    entity_id: str
    state: Any
    attributes: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
