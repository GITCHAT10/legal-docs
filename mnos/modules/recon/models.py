from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class SecurityEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str # MOTION_DETECTED, DOOR_OPENED, etc.
    source_id: str
    location: str
    timestamp: datetime = Field(default_factory=datetime.now)
    severity: str = "INFO"

class Incident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    status: str = "OPEN" # OPEN, ACKNOWLEDGED, IN_PROGRESS, RESOLVED
    events: List[SecurityEvent] = Field(default_factory=list)
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class IncidentManagementSystem:
    def __init__(self, shadow_logger):
        self.incidents: Dict[str, Incident] = {}
        self.shadow_logger = shadow_logger

    def create_incident(self, title: str, severity: str, events: List[SecurityEvent]) -> Incident:
        incident = Incident(title=title, severity=severity, events=events)
        self.incidents[incident.id] = incident

        # Log to SHADOW
        self.shadow_logger.log("INCIDENT_CREATED", incident.model_dump())
        return incident

    def update_status(self, incident_id: str, status: str, user: str):
        if incident_id in self.incidents:
            incident = self.incidents[incident_id]
            incident.status = status
            incident.updated_at = datetime.now()

            # Log to SHADOW
            self.shadow_logger.log("INCIDENT_STATUS_UPDATED", {
                "id": incident_id,
                "status": status,
                "user": user
            })
