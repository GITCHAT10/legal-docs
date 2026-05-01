from mnos.modules.ut_aeromarine.mission_schema import UTAMMission, MissionStatus, LaunchPlatform
import logging

logger = logging.getLogger("UT_AEROMARINE_COMPLIANCE")

class ComplianceGate:
    """
    UT AEROMARINE Compliance Gate.
    Enforces MNOS Operating Rules for hybrid air-sea operations.
    """
    def __init__(self, authority, device_registry, shadow):
        self.authority = authority
        self.device_registry = device_registry
        self.shadow = shadow

    async def validate_for_launch(self, mission: UTAMMission) -> bool:
        """
        Final compliance check before mission launch.
        """
        # Rule: Operator authority
        if not await self.authority.has_authority(mission.operator_id, mission.mission_type):
            raise PermissionError(f"FAIL CLOSED: Operator {mission.operator_id} lacks authority for {mission.mission_type}")

        # Rule: Registered and Active Device
        if not self.device_registry.is_device_ready(mission.device_id):
            raise RuntimeError(f"FAIL CLOSED: Device {mission.device_id} is not registered or active")

        # Rule: CAA Approval
        if not mission.caa_approval_ref:
            raise RuntimeError("FAIL CLOSED: Missing CAA approval reference")

        # Rule: Airspace Clearance
        if not mission.airspace_clearance_id:
            raise RuntimeError("FAIL CLOSED: Missing airspace clearance")

        # Rule: Route Plan & Geofence
        if not mission.route_plan or not mission.geofence_zone:
            raise RuntimeError("FAIL CLOSED: Missing route plan or geofence")

        # Rule: Dynamic Home Point for Boat Launch
        if mission.launch_platform in [LaunchPlatform.BOAT, LaunchPlatform.PATROL_VESSEL]:
            if not mission.dynamic_home_point_enabled:
                raise RuntimeError(f"FAIL CLOSED: Dynamic home point required for launch from {mission.launch_platform.value}")

        # Rule: SHADOW Trace
        if not mission.shadow_trace_id:
            raise RuntimeError("FAIL CLOSED: Missing SHADOW trace ID before launch")

        mission.status = MissionStatus.READY
        return True
