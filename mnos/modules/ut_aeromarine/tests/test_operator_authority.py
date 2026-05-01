import pytest
from mnos.modules.ut_aeromarine.mission_schema import MissionType, AssetType

@pytest.mark.asyncio
async def test_operator_authority_denied(utam_stack):
    planner, _, _, _, _ = utam_stack
    # MALDIVES-MAPPING-01 is only authorized for MAPPING/SURVEY
    mission = await planner.create_mission("MALDIVES-MAPPING-01", MissionType.QRD_RESPONSE, AssetType.QRD_DRONE)
    with pytest.raises(PermissionError) as exc:
        await planner.launch_mission(mission.mission_id, "QRD-UTAM-01")
    assert "lacks authority" in str(exc.value)

@pytest.mark.asyncio
async def test_operator_not_in_registry(utam_stack):
    planner, _, _, _, _ = utam_stack
    mission = await planner.create_mission("ROGUE-OP", MissionType.QRD_RESPONSE, AssetType.QRD_DRONE)
    with pytest.raises(PermissionError):
        await planner.launch_mission(mission.mission_id, "QRD-UTAM-01")
