from enum import Enum
from typing import List, Dict

class EmergencyButton(Enum):
    DROWNING = "DROWNING"
    MEDICAL = "MEDICAL"
    FIRE_SMOKE = "FIRE_SMOKE"
    MISSING_GUEST = "MISSING_GUEST"
    JETTY_BOAT_INCIDENT = "JETTY_BOAT_INCIDENT"
    SECURITY_ALERT = "SECURITY_ALERT"
    STORM_DAMAGE = "STORM_DAMAGE"
    EVACUATION_SUPPORT = "EVACUATION_SUPPORT"
    CROWD_RISK = "CROWD_RISK"
    TRAFFIC_INCIDENT = "TRAFFIC_INCIDENT"

EMERGENCY_WORKFLOWS = {
    "DROWNING": ["Alert Registration", "Drone Dispatch", "Lifeguard Notification", "MNDF Escalation"],
    "MEDICAL": ["Triage", "Ambulance/Boat Dispatch", "Hospital Coordination"],
    "FIRE_SMOKE": ["Verification Flight", "Fire Dept Notification", "Evacuation Readiness"],
    "MISSING_GUEST": ["Search Grid Generation", "Fleet Dispatch", "Police Coordination"],
    "JETTY_BOAT_INCIDENT": ["Incident Capture", "Maritime Escalation", "Evidence Sealing"]
}
