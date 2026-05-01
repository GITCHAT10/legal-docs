import pytest
from mnos.modules.ut_aeromarine.mission_schema import MissionType, AssetType

@pytest.mark.asyncio
async def test_device_registration_required(utam_stack):
    planner, _, _, _, _ = utam_stack
    mission = await planner.create_mission("MIG-ADMIN-01", MissionType.QRD_RESPONSE, AssetType.QRD_DRONE)

    # Valid approvals but UNKNOWN device
    mission.caa_approval_ref = "C"
    mission.airspace_clearance_id = "A"
    mission.route_plan = [(0,0)]
    mission.geofence_zone = "G"
    mission.shadow_trace_id = "S"

    with pytest.raises(RuntimeError) as exc:
        await planner.launch_mission(mission.mission_id, "UNKNOWN-DRONE")
    assert "not registered" in str(exc.value)
