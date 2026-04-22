from typing import Dict, List, Any
from mnos.modules.recon.incident import MarsIncidentEngine
from mnos.modules.recon.threat import MarsThreatEngine, MarsPanicSystem

class MarsReconnaissanceCore:
    """
    MARS RECONNAISSANCE CORE: Unified security layer.
    """
    def __init__(self, shadow_logger, event_bus):
        self.incident_engine = MarsIncidentEngine(shadow_logger, event_bus)
        self.threat_engine = MarsThreatEngine(self.incident_engine)
        self.panic_system = MarsPanicSystem(self.incident_engine)

    def get_command_center_data(self) -> Dict[str, Any]:
        """
        API Output for Command Center.
        """
        active_incidents = [i.model_dump() for i in self.incident_engine.incidents.values() if i.status != "RESOLVED"]
        return {
            "active_incidents_count": len(active_incidents),
            "high_severity_incidents": [i for i in active_incidents if i["severity"] in ["HIGH", "CRITICAL"]],
            "system_status": "OPERATIONAL",
            "patrol_units": "STANDBY"
        }
