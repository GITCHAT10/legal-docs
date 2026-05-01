from mnos.modules.ut_aeromarine.mission_schema import UTAMMission, MissionStatus
import logging
import asyncio

logger = logging.getLogger("UT_AEROMARINE_PLANNER")

class MissionPlanner:
    """
    UT AEROMARINE Mission Planner.
    Handles mission creation, approval workflow, and execution loop.
    """
    def __init__(self, compliance, shadow_logger, watchdog, events):
        self.compliance = compliance
        self.shadow_logger = shadow_logger
        self.watchdog = watchdog
        self.events = events
        self.active_missions = {}

    async def create_mission(self, operator_id: str, mission_type, asset_type) -> UTAMMission:
        mission = UTAMMission(
            operator_id=operator_id,
            mission_type=mission_type,
            asset_type=asset_type
        )
        self.shadow_logger.log_transition(mission, "MISSION_CREATED")
        self.active_missions[mission.mission_id] = mission
        return mission

    async def approve_route(self, mission_id: str, route_plan: list, geofence: str, altitude: float):
        mission = self.active_missions.get(mission_id)
        if not mission: raise ValueError("Mission not found")

        mission.route_plan = route_plan
        mission.geofence_zone = geofence
        mission.altitude_limit = altitude

        self.shadow_logger.log_transition(mission, "ROUTE_VALIDATED")
        return True

    async def attach_approvals(self, mission_id: str, caa_ref: str, airspace_id: str, mndf_ref: str = None):
        mission = self.active_missions.get(mission_id)
        if not mission: raise ValueError("Mission not found")

        mission.caa_approval_ref = caa_ref
        mission.airspace_clearance_id = airspace_id
        mission.mndf_approval_ref = mndf_ref

        self.shadow_logger.log_transition(mission, "APPROVAL_ATTACHED")
        return True

    async def launch_mission(self, mission_id: str, device_id: str):
        mission = self.active_missions.get(mission_id)
        if not mission: raise ValueError("Mission not found")

        mission.device_id = device_id

        # FINAL COMPLIANCE GATE
        await self.compliance.validate_for_launch(mission)

        # ARMING
        self.watchdog.update_heartbeat(device_id)
        self.shadow_logger.log_transition(mission, "TELEMETRY_WATCHDOG_ARMED")

        # LAUNCH
        mission.status = MissionStatus.LAUNCHED
        self.shadow_logger.log_transition(mission, "MISSION_LAUNCHED")

        return {"status": "LAUNCHED", "mission_id": mission_id}
