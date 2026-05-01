import pytest
from mnos.modules.ut_aeromarine.mission_schema import MissionType, AssetType, LaunchPlatform

@pytest.mark.asyncio
async def test_dynamic_home_point_required_for_boat(utam_stack):
    planner, _, _, _, _ = utam_stack
    mission = await planner.create_mission("MIG-ADMIN-01", MissionType.QRD_RESPONSE, AssetType.BOAT_LAUNCHED_DRONE)
    mission.launch_platform = LaunchPlatform.BOAT
    mission.caa_approval_ref = "C"
    mission.airspace_clearance_id = "A"
    mission.route_plan = [(0,0)]
    mission.geofence_zone = "G"
    mission.shadow_trace_id = "S"

    # Missing dynamic home
    with pytest.raises(RuntimeError) as exc:
        await planner.launch_mission(mission.mission_id, "QRD-UTAM-01")
    assert "Dynamic home point required" in str(exc.value)

    # Enable it
    mission.dynamic_home_point_enabled = True
    res = await planner.launch_mission(mission.mission_id, "QRD-UTAM-01")
    assert res["status"] == "LAUNCHED"
