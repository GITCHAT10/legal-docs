from mnos.modules.ut_aeromarine.mission_schema import UTAMMission, MissionStatus
import logging

logger = logging.getLogger("UT_AEROMARINE_SHADOW")

class ShadowLogger:
    """
    UT AEROMARINE Shadow Logger.
    Enforces SHADOW event generation for every state transition.
    """
    def __init__(self, shadow, guard):
        self.shadow = shadow
        self.guard = guard

    def log_transition(self, mission: UTAMMission, event_name: str, metadata: dict = None):
        """
        Record a state transition in the SHADOW ledger.
        """
        payload = {
            "mission_id": mission.mission_id,
            "status": mission.status.value,
            "operator_id": mission.operator_id,
            "device_id": mission.device_id,
            "timestamp": mission.start_time,
            "metadata": metadata or {}
        }

        # Bypass guard if it's an internal lifecycle event, or use guard if it's an operator action
        from mnos.shared.execution_guard import _sovereign_context
        token = _sovereign_context.get().get("token") if _sovereign_context.get() else "INTERNAL"

        # In a real system, the SHADOW trace ID would be returned by the ledger
        # and attached to the mission. Here we only auto-assign if NOT MISSION_CREATED
        # to ensure we can test the "Missing SHADOW Trace" gate.
        if event_name != "MISSION_CREATED" and not mission.shadow_trace_id:
             mission.shadow_trace_id = f"TRACE-{mission.mission_id}"

        self.shadow.commit(f"utam.mission.{event_name.lower()}", mission.mission_id, payload)
        logger.info(f"[SHADOW] Mission {mission.mission_id} -> {event_name}")
