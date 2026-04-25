from typing import Dict, Any
from mnos.shared.execution_guard import guard

class UrbanCore:
    """
    MALE_URBAN_INTELLIGENCE:
    Traffic Signal & Emergency Corridor Management.
    """
    def set_signal_state(self, signal_id: str, state: str, session_context: Dict[str, Any]):
        def commit_signal(payload):
            print(f"[Urban] Signal {payload['signal_id']} set to {payload['state']}")
            return {"status": "SIGNAL_UPDATED", "signal_id": payload['signal_id'], "state": payload['state']}

        return guard.execute_sovereign_action(
            "urban.signal_updated",
            {"signal_id": signal_id, "state": state},
            session_context,
            commit_signal
        )

class EmergencyShield:
    """
    MALE_EMERGENCY_SHIELD:
    Hospital/Police priority grid isolation.
    """
    def activate_priority_corridor(self, route_id: str, session_context: Dict[str, Any]):
        def commit_priority(payload):
            print(f"[Urban] Priority Corridor {payload['route_id']} ACTIVATED")
            return {"status": "CORRIDOR_ACTIVE", "route_id": payload['route_id']}

        return guard.execute_sovereign_action(
            "urban.priority_corridor_active",
            {"route_id": route_id},
            session_context,
            commit_priority
        )

urban_core = UrbanCore()
emergency_shield = EmergencyShield()
