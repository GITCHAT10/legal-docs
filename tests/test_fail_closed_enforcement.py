import pytest
import os
import subprocess
import sys
from fastapi.testclient import TestClient

def test_nexgen_secret_enforcement():
    """TASK 2: Missing NEXGEN_SECRET -> startup MUST FAIL"""
    # Use a subprocess to avoid polluting the current process and breaking other tests
    env = os.environ.copy()
    if "NEXGEN_SECRET" in env:
        del env["NEXGEN_SECRET"]

    # Try to run main.py as a script
    result = subprocess.run(
        [sys.executable, "main.py"],
        env=env,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
    assert "FAIL CLOSED: NEXGEN_SECRET is required for startup" in result.stderr

def test_event_bus_unauthorized():
    """TASK 1: EventBus without ExecutionGuard -> MUST FAIL"""
    from mnos.modules.events.bus import DistributedEventBus
    bus = DistributedEventBus()

    with pytest.raises(PermissionError) as excinfo:
        bus.publish("SENSITIVE_EVENT", {"data": "secret"})
    assert "FAIL CLOSED: Direct event publish blocked" in str(excinfo.value)

    # Test allowlist bypass
    assert bus.publish("IDENTITY_CREATED", {"user": "test"}) is True

def test_pricing_validation_tourism():
    """TASK 3: Booking without price -> MUST FAIL"""
    from main import app, identity_core
    client = TestClient(app)

    # Setup actor
    actor_id = "TEST-ACTOR-FAIL-CLOSED"
    identity_core.profiles[actor_id] = {"profile_type": "customer", "organization_id": "TEST"}
    identity_core.bind_device(actor_id, {"fingerprint": "dev-01-fail-closed"})
    dev_id = list(identity_core.devices.keys())[-1]
    identity_core.verify_identity(actor_id, "SYSTEM")

    headers = {
        "X-AEGIS-IDENTITY": actor_id,
        "X-AEGIS-DEVICE": dev_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"
    }

    # Missing price
    payload = {"package_id": "PKG-01"}
    response = client.post("/imoxon/tourism/book", json=payload, headers=headers)

    assert response.status_code == 400
    assert "Missing price" in response.json()["detail"]
