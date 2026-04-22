from typing import Dict, Any, List

class MarsCommandGrid:
    """
    MARS COMMAND GRID: Unified control interface for the Execution Layer.
    Controls IOT, Recon, and Scenes via MNOS Core.
    """
    def __init__(self, hub, recon_core, scene_engine):
        self.hub = hub
        self.recon_core = recon_core
        self.scene_engine = scene_engine

    def get_status_overview(self) -> Dict[str, Any]:
        """
        Unified View: Security + IOT + Automation.
        """
        return {
            "security": self.recon_core.get_command_center_data(),
            "automation_active": True,
            "local_hub_status": "ONLINE",
            "active_incidents": len(self.recon_core.incident_engine.incidents)
        }

    def trigger_panic(self, location: str, user_id: str):
        return self.recon_core.panic_system.trigger(location, user_id)
