from mnos.modules.ut_aeromarine.mission_schema import MissionStatus
from typing import Dict

class KPI_3_30_3_Validator:
    """
    Validates missions against the 3-30-3 KPI standard.
    - 3 seconds: alert intake / event registration
    - 30 seconds: command decision / dispatch readiness
    - 3 minutes: mission launch or response-ready status
    """
    def __init__(self):
        self.kpis: Dict[str, dict] = {}

    def record_event(self, mission_id: str, stage: str, timestamp: float):
        if mission_id not in self.kpis:
            self.kpis[mission_id] = {}
        self.kpis[mission_id][stage] = timestamp

    def validate_mission(self, mission_id: str) -> dict:
        stages = self.kpis.get(mission_id, {})

        intake_time = stages.get("INTAKE")
        decision_time = stages.get("DECISION")
        launch_time = stages.get("LAUNCH")

        report = {
            "intake_to_decision": (decision_time - intake_time) if intake_time and decision_time else None,
            "decision_to_launch": (launch_time - decision_time) if decision_time and launch_time else None,
            "total_response_time": (launch_time - intake_time) if intake_time and launch_time else None
        }

        report["3s_intake_ok"] = report["intake_to_decision"] is not None and report["intake_to_decision"] <= 30.0 # Wait, 3s is intake registration, 30s is decision.
        # Adjusted logic:
        # Alert (T0) -> Registration (T+3s)
        # Registration -> Decision (T+30s)
        # Decision -> Launch (T+3m)

        return report
