import pytest
from mnos.modules.ut_aeromarine.mission_schema import MissionType, AssetType

@pytest.mark.asyncio
async def test_airspace_clearance_required(utam_stack):
    planner, _, _, _, _ = utam_stack
    mission = await planner.create_mission("MIG-ADMIN-01", MissionType.QRD_RESPONSE, AssetType.QRD_DRONE)
    mission.caa_approval_ref = "C"
    # Missing Airspace

    with pytest.raises(RuntimeError) as exc:
        await planner.launch_mission(mission.mission_id, "QRD-UTAM-01")
    assert "Missing airspace clearance" in str(exc.value)
