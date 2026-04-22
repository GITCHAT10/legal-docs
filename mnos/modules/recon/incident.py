from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class MarsSecurityEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str # MOTION_DETECTED, DOOR_FORCED, CAMERA_ALERT
    source_id: str
    location: str
    timestamp: datetime = Field(default_factory=datetime.now)
    severity: str = "INFO"

class MarsIncident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    status: str = "OPEN" # OPEN, ACKNOWLEDGED, RESOLVED
    events: List[MarsSecurityEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

class MarsIncidentEngine:
    def __init__(self, shadow_logger, event_bus):
        self.incidents: Dict[str, MarsIncident] = {}
        self.shadow_logger = shadow_logger
        self.event_bus = event_bus

    def raise_incident(self, title: str, severity: str, events: List[MarsSecurityEvent]) -> MarsIncident:
        incident = MarsIncident(title=title, severity=severity, events=events)
        self.incidents[incident.id] = incident

        # Log to MNOS SHADOW
        self.shadow_logger.log("MARS_INCIDENT_RAISED", incident.model_dump())

        # Emit to EVENTS
        self.event_bus.emit("MARS_INCIDENT_ALERT", incident.model_dump())

        return incident
