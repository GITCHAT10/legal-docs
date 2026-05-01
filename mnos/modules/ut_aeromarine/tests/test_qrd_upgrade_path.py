import pytest
import os
from main import app, guard, shadow_core, identity_core, fce_core, events_core
from mnos.modules.ut_aeromarine.mission_schema import MissionType, AssetType, MissionStatus
from mnos.modules.ut_aeromarine.device_registry import DeviceRegistry
from mnos.modules.ut_aeromarine.operator_authority import OperatorAuthority
from mnos.modules.ut_aeromarine.compliance_gate import ComplianceGate
from mnos.modules.ut_aeromarine.shadow_logger import ShadowLogger
from mnos.modules.ut_aeromarine.telemetry_watchdog import TelemetryWatchdog
from mnos.modules.ut_aeromarine.mission_planner import MissionPlanner
from mnos.modules.ut_aeromarine.fce_billing_gate import FCEBillingGate

@pytest.fixture
def utam_stack():
    # Setup AEGIS identity for MIG-ADMIN-01 if missing
    if "MIG-ADMIN-01" not in identity_core.profiles:
        identity_core.profiles["MIG-ADMIN-01"] = {"profile_type": "admin"}

    registry = DeviceRegistry(shadow_core)
    authority = OperatorAuthority(identity_core)
    shadow_log = ShadowLogger(shadow_core, guard)
    watchdog = TelemetryWatchdog(shadow_core)
    planner = MissionPlanner(ComplianceGate(authority, registry, shadow_core), shadow_log, watchdog, events_core)
    billing = FCEBillingGate(fce_core, shadow_core)

    # Register a test device
    registry.register_device("QRD-UTAM-01", {"type": "DRONE"})

    return planner, registry, authority, watchdog, billing

@pytest.mark.asyncio
async def test_qrd_v1_compatibility(utam_stack):
    planner, _, _, _, _ = utam_stack
    # Existing QRD v1 logic (simplified dispatch)
    mission = await planner.create_mission("MIG-ADMIN-01", MissionType.QRD_RESPONSE, AssetType.QRD_DRONE)
    assert mission.status == MissionStatus.DRAFT

@pytest.mark.asyncio
async def test_missing_aegis_operator_blocks_launch(utam_stack):
    planner, _, _, _, _ = utam_stack
    mission = await planner.create_mission("UNKNOWN-OP", MissionType.QRD_RESPONSE, AssetType.QRD_DRONE)
    with pytest.raises(PermissionError):
        await planner.launch_mission(mission.mission_id, "QRD-UTAM-01")

@pytest.mark.asyncio
async def test_unauthorized_mission_type_blocks_launch(utam_stack):
    planner, _, _, _, _ = utam_stack
    # MALDIVES-MAPPING-01 is not authorized for QRD_RESPONSE
    mission = await planner.create_mission("MALDIVES-MAPPING-01", MissionType.QRD_RESPONSE, AssetType.QRD_DRONE)
    with pytest.raises(PermissionError):
        await planner.launch_mission(mission.mission_id, "QRD-UTAM-01")

@pytest.mark.asyncio
async def test_missing_caa_blocks_mission(utam_stack):
    planner, _, _, _, _ = utam_stack
    mission = await planner.create_mission("MIG-ADMIN-01", MissionType.QRD_RESPONSE, AssetType.QRD_DRONE)
    # Missing Route/Geofence/CAA
    with pytest.raises(RuntimeError) as exc:
        await planner.launch_mission(mission.mission_id, "QRD-UTAM-01")
    assert "Missing CAA" in str(exc.value)

@pytest.mark.asyncio
async def test_full_compliance_path_success(utam_stack):
    planner, _, _, _, _ = utam_stack
    mission = await planner.create_mission("MIG-ADMIN-01", MissionType.QRD_RESPONSE, AssetType.QRD_DRONE)

    await planner.approve_route(mission.mission_id, [(0,0), (1,1)], "GAN-ZONE-A", 100.0)
    await planner.attach_approvals(mission.mission_id, "CAA-2026-99", "AIR-992")

    # Must have shadow trace
    mission.shadow_trace_id = "TRACE-99"

    res = await planner.launch_mission(mission.mission_id, "QRD-UTAM-01")
    assert res["status"] == "LAUNCHED"
    assert mission.status == MissionStatus.LAUNCHED

@pytest.mark.asyncio
async def test_telemetry_watchdog_fail_closed(utam_stack):
    planner, _, _, watchdog, _ = utam_stack
    device_id = "QRD-UTAM-01"

    watchdog.update_heartbeat(device_id)
    assert watchdog.check_safety(device_id, {"battery": 80, "gps_lock": True}) is True

    # Simulate loss (wait >3s is not practical for unit test, so we mock time or just manually expire)
    import time
    watchdog.heartbeats[device_id] = time.time() - 10.0
    assert watchdog.check_safety(device_id, {"battery": 80}) is False

@pytest.mark.asyncio
async def test_billing_locked_until_sealed(utam_stack):
    _, _, _, _, billing = utam_stack
    from mnos.modules.ut_aeromarine.mission_schema import UTAMMission
    mission = UTAMMission(mission_id="M-BILL-01", commercial_billable=True)

    with pytest.raises(RuntimeError) as exc:
        billing.release_billing(mission)
    assert "not SHADOW_SEALED" in str(exc.value)

    mission.status = MissionStatus.SHADOW_SEALED
    mission.shadow_trace_id = "TRACE-B"
    res = billing.release_billing(mission)
    assert res["status"] == "BILLING_RELEASED"

def test_missing_price_regression():
    # Proof for critical fix #3
    from mnos.modules.tourism.engine import TourismEngine
    from unittest.mock import MagicMock
    core = MagicMock()
    tourism = TourismEngine(core)
    with pytest.raises(ValueError):
        tourism._internal_book({"package_id": "P1"})
