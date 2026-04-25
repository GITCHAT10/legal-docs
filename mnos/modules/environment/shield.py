from typing import Dict, Any
from mnos.shared.execution_guard import guard

class EnvironmentalShield:
    """
    MARS_ENVIRONMENTAL_SHIELD (MALE WATER NETWORK):
    Logic: Segment isolation on Pressure/Flow anomaly.
    """
    def process_sensor_event(self, sensor_data: Dict[str, Any], session_context: Dict[str, Any]):
        """
        Pressure/Flow threshold trigger validation.
        """
        pressure = sensor_data.get("pressure_psi", 0)
        flow = sensor_data.get("flow_rate", 0)

        # P1: No full network shutdown, segment isolation only
        def isolate_segment(payload):
            print(f"[EnvShield] INFRA FAILURE: Segment {payload['segment']} ISOLATED. Supply maintained to adjacent zones.")
            return {"status": "SEGMENT_ISOLATED", "segment": payload['segment']}

        if pressure > 150 or flow > 500:
             return guard.execute_sovereign_action(
                "environment.infra_failure",
                {
                    "pressure": pressure,
                    "flow": flow,
                    "segment": sensor_data.get("segment_id", "S-01"),
                    "safety_logic": "SEGMENT_ISOLATION_ONLY"
                },
                session_context,
                isolate_segment
            )
        return {"status": "NORMAL"}

env_shield = EnvironmentalShield()
