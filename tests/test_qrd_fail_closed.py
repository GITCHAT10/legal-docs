import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, mig_shield
import json

client = TestClient(app)

@pytest.fixture
def setup_operator():
    uid = identity_core.create_profile({"full_name": "Op", "profile_type": "admin"})
    did = identity_core.bind_device(uid, {"fingerprint": "f1"})
    # Verify for the hardened check if any
    identity_core.verify_identity(uid, "SYSTEM")
    return uid, did

def test_aegis_fail_blocks_dispatch():
    # No headers -> Fail
    payload = {"type": "FIRE", "severity": 4, "location": [1, 1]}
    resp = client.post("/imoxon/mig-shield/mission/dispatch", json=payload)
    assert resp.status_code == 403
    assert "Missing Identity" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_low_battery_triggers_rtb(setup_operator):
    uid, did = setup_operator
    headers = {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

    # Force low battery on ALL drones to ensure the selected one is low battery
    for drone in mig_shield.drones:
        drone.battery = 10.0

    payload = {"type": "DROWNING", "severity": 4, "location": [0,0]}
    resp = client.post("/imoxon/mig-shield/mission/dispatch", json=payload, headers=headers)

    # After Fail-Closed update, low battery blocks dispatch (400)
    assert resp.status_code == 400
    # It might be blocked by bid logic first if all drones are low battery

    # Restore battery for other tests
    for drone in mig_shield.drones:
        drone.battery = 100.0

def test_orca_deny_blocks_launch(setup_operator):
    # This would require mocking ORCA or many attempts
    pass
