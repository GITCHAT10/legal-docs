import pytest
from mnos.modules.ut_aeromarine.mission_schema import UTAMMission, MissionStatus
import time

@pytest.mark.asyncio
async def test_telemetry_watchdog_heartbeat_loss(utam_stack):
    _, _, _, watchdog, _ = utam_stack
    device_id = "QRD-1"

    watchdog.update_heartbeat(device_id)
    assert watchdog.check_safety(device_id, {}) is True

    # Simulate loss
    watchdog.heartbeats[device_id] = time.time() - 5.0
    assert watchdog.check_safety(device_id, {}) is False

@pytest.mark.asyncio
async def test_telemetry_watchdog_geofence_breach(utam_stack):
    _, _, _, watchdog, _ = utam_stack
    device_id = "QRD-1"

    watchdog.update_heartbeat(device_id)
    assert watchdog.check_safety(device_id, {"geofence_ok": False}) is False
