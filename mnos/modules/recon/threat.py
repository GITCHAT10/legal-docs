from typing import List, Dict, Any
from mnos.modules.recon.incident import MarsSecurityEvent, MarsIncident

class MarsThreatEngine:
    """
    MARS THREAT ENGINE: Event correlation and incident generation.
    """
    def __init__(self, incident_engine):
        self.incident_engine = incident_engine
        self.event_history: List[MarsSecurityEvent] = []

    def process_security_event(self, event: MarsSecurityEvent):
        self.event_history.append(event)

        # Simple Correlation: Motion + Door Forced in same location within buffer
        if event.event_type == "DOOR_FORCED":
            recent_motion = [e for e in self.event_history
                             if e.event_type == "MOTION_DETECTED"
                             and e.location == event.location]

            if recent_motion:
                print(f"🚨 MARS THREAT DETECTED in {event.location}")
                self.incident_engine.raise_incident(
                    title=f"Intrusion Detected: {event.location}",
                    severity="CRITICAL",
                    events=[recent_motion[-1], event]
                )

        if len(self.event_history) > 100:
            self.event_history.pop(0)

class MarsPanicSystem:
    """
    MARS PANIC SYSTEM: Sovereign SOS and Incident Trigger.
    """
    def __init__(self, incident_engine):
        self.incident_engine = incident_engine

    def trigger(self, location: str, user_id: str):
        print(f"🆘 MARS PANIC TRIGGERED by {user_id} in {location}")
        event = MarsSecurityEvent(event_type="SOS_TRIGGERED", source_id=user_id, location=location, severity="CRITICAL")
        return self.incident_engine.raise_incident(
            title=f"Panic Alarm: {location}",
            severity="CRITICAL",
            events=[event]
        )
