import pytest
from fastapi.testclient import TestClient
import os
import uuid
import random
from main import app, identity_core, mig_shield, orca

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def setup_bootstrap():
    os.environ["NEXGEN_SECRET"] = "gate-verification-2026"
    # Ensure CMD-HUB-01 is bound to MIG-ADMIN-01
    demo_id = "MIG-ADMIN-01"
    if demo_id not in identity_core.profiles:
        identity_core.profiles[demo_id] = {
            "identity_id": demo_id,
            "profile_type": "admin",
            "full_name": "MIG Command Admin",
            "organization_id": "MIG-HQ"
        }
    identity_core.bind_device(demo_id, {"fingerprint": "CMD-HUB-01"})
    # Correct device ID for the test client
    dev_id = list(identity_core.devices.keys())[-1]
    identity_core.devices["CMD-HUB-01"] = identity_core.devices.pop(dev_id)
    identity_core.devices["CMD-HUB-01"]["device_id"] = "CMD-HUB-01"
    identity_core.verify_identity(demo_id, "SYSTEM")

def get_auth_headers(identity_id="MIG-ADMIN-01"):
    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": "CMD-HUB-01",
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

def test_gate_01_normal_dispatch():
    """1. Normal dispatch -> Success path"""
    import unittest.mock as mock
    # Force ORCA to allow to avoid intermittent 5% failure
    with mock.patch.object(orca, 'validate_mission', return_value={"allowed": True, "reason": "CLEAR"}):
        payload = {"type": "DROWNING", "severity": 4, "location": [1.0, 2.0]}
        response = client.post("/imoxon/mig-shield/mission/dispatch", json=payload, headers=get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
    assert "incident_id" in data
    assert "drone_id" in data

def test_gate_02_aegis_failure():
    """2. AEGIS failure -> FAIL_CLOSED"""
    payload = {"type": "FIRE", "severity": 4, "location": [1.0, 2.0]}
    # Case A: Missing headers
    response = client.post("/imoxon/mig-shield/mission/dispatch", json=payload)
    assert response.status_code == 403

    # Case B: Invalid signature
    headers = get_auth_headers()
    headers["X-AEGIS-SIGNATURE"] = "MALICIOUS_SIG"
    response = client.post("/imoxon/mig-shield/mission/dispatch", json=payload, headers=headers)
    assert response.status_code == 403

def test_gate_03_orca_denial():
    """3. ORCA denial -> blocked mission"""
    # Force ORCA to deny by mocking internal state or just repeating until it hits the 5% failure rate
    # But for a reliable test, we'll patch the orca.validate_mission
    import unittest.mock as mock
    with mock.patch.object(orca, 'validate_mission', return_value={"allowed": False, "reason": "WEATHER_RESTRICTED"}):
        payload = {"type": "MEDICAL", "severity": 4, "location": [1.0, 2.0]}
        response = client.post("/imoxon/mig-shield/mission/dispatch", json=payload, headers=get_auth_headers())
        assert response.status_code == 400 or response.status_code == 500
        assert "WEATHER_RESTRICTED" in response.json()["detail"]

def test_gate_04_telemetry_loss():
    """4. Telemetry loss >3s -> auto-RTB"""
    import unittest.mock as mock
    drone = mig_shield.drones[0]
    # We force the bridge to report inactive for this drone
    with mock.patch.object(mig_shield.telemetry_bridge, 'is_active', return_value=False):
        payload = {"type": "DROWNING", "severity": 4, "location": [1.0, 2.0]}
        response = client.post("/imoxon/mig-shield/mission/dispatch", json=payload, headers=get_auth_headers())
        # Returning status=ABORTED_RTB results in 200 OK since it's a handled safe state
        assert response.status_code == 200
        assert response.json()["status"] == "ABORTED_RTB"
        assert response.json()["reason"] == "TELEMETRY_LOST"

def test_gate_05_low_battery():
    """5. Low battery -> no launch or abort"""
    # Force ALL drones battery low
    for drone in mig_shield.drones:
        drone.battery = 10.0

    drone = mig_shield.drones[0]
    original_battery = drone.battery
    drone.battery = 10.0
    try:
        payload = {"type": "DROWNING", "severity": 4, "location": [1.0, 2.0]}
        response = client.post("/imoxon/mig-shield/mission/dispatch", json=payload, headers=get_auth_headers())
        # Should be blocked
        assert "LOW_BATTERY_DISPATCH_BLOCKED" in response.text
    finally:
        for drone in mig_shield.drones:
            drone.battery = 100.0

def test_gate_06_sdk_timeout():
    """6. SDK timeout / adapter error -> safe state"""
    # Mock ALL adapters failure
    import unittest.mock as mock

    # We patch ORCA to always allow for this test
    with mock.patch.object(orca, 'validate_mission', return_value={"allowed": True, "reason": "CLEAR"}):
        # We patch the adapters for all drones to ensure the one picked fails
        mocks = [mock.patch.object(d.adapter, 'connect', side_effect=Exception("Connection Timeout")) for d in mig_shield.drones]
        for m in mocks: m.start()
        try:
            payload = {"type": "DROWNING", "severity": 4, "location": [1.0, 2.0]}
            response = client.post("/imoxon/mig-shield/mission/dispatch", json=payload, headers=get_auth_headers())
            assert "SDK Error" in response.text
        finally:
            for m in mocks: m.stop()
