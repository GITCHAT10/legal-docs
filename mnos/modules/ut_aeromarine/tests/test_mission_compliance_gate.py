import pytest
from mnos.modules.ut_aeromarine.mission_schema import UTAMMission, MissionType, AssetType
from mnos.modules.ut_aeromarine.compliance_gate import ComplianceGate

@pytest.mark.asyncio
async def test_compliance_gate_blocks_without_caa(utam_stack):
    planner, _, _, _, _ = utam_stack
    mission = await planner.create_mission("MIG-ADMIN-01", MissionType.QRD_RESPONSE, AssetType.QRD_DRONE)

    # Missing CAA
    with pytest.raises(RuntimeError) as exc:
        await planner.launch_mission(mission.mission_id, "QRD-UTAM-01")
    assert "Missing CAA" in str(exc.value)

@pytest.mark.asyncio
async def test_compliance_gate_blocks_without_route(utam_stack):
    planner, _, _, _, _ = utam_stack
    mission = await planner.create_mission("MIG-ADMIN-01", MissionType.QRD_RESPONSE, AssetType.QRD_DRONE)
    mission.caa_approval_ref = "CAA-1"
    mission.airspace_clearance_id = "AIR-1"

    # Missing Route/Geofence
    with pytest.raises(RuntimeError) as exc:
        await planner.launch_mission(mission.mission_id, "QRD-UTAM-01")
    assert "Missing route plan" in str(exc.value)
