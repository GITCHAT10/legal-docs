import pytest
from fastapi.testclient import TestClient
import os
import mnos.shared.execution_guard as eg
from datetime import datetime, UTC, timedelta

# Set dummy secret
os.environ["NEXGEN_SECRET"] = "TEST-SECRET"

from main import app, identity_core

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_auth():
    # Authorize setup
    eg._sovereign_context.set({"token": "setup", "actor": {"identity_id": "system", "device_id": "sys"}})
    yield
    eg._sovereign_context.set(None)

def test_payout_rejects_unknown_quote_id():
    identity_id = "test-fin-1"
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": "dev-fin-1",
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }
    identity_core.profiles[identity_id] = {"profile_type": "UT_FINANCE", "verification_status": "verified"}
    identity_core.devices["dev-fin-1"] = {"identity_id": identity_id}

    response = client.post("/imoxon/ut/fce/payout/release?quote_id=unknown&orca=true&shadow=true&apollo=true", headers=headers)
    assert response.status_code == 404
    assert "QUOTE_NOT_FOUND" in response.json()["detail"]

def test_safety_gate_rejects_expired_insurance():
    identity_id = "test-saf-1"
    identity_core.profiles[identity_id] = {"profile_type": "UT_SAFETY", "verification_status": "verified"}
    identity_core.devices["dev-saf-1"] = {"identity_id": identity_id}

    from main import ut_safety_gate

    actor = {"identity_id": identity_id, "device_id": "dev-saf-1", "role": "UT_SAFETY"}

    # Past date
    expired_date = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    asset_data = {"capacity": 20, "passenger_count": 10, "captain_status": "VERIFIED", "lifejacket_count": 20, "insurance_expiry": expired_date}
    weather_data = {"sea_state": 1}

    result = ut_safety_gate.validate_dispatch(actor, asset_data, weather_data)
    assert not result["checks"]["insurance_valid"]
    assert result["gate_status"] == "BLOCKED"

def test_safety_gate_rejects_missing_insurance_expiry():
    from main import ut_safety_gate
    actor = {"identity_id": "sys", "device_id": "sys", "role": "UT_SAFETY"}
    asset_data = {"capacity": 20, "passenger_count": 10, "captain_status": "VERIFIED", "lifejacket_count": 20}
    weather_data = {"sea_state": 1}
    result = ut_safety_gate.validate_dispatch(actor, asset_data, weather_data)
    assert not result["checks"]["insurance_valid"]
    assert result["gate_status"] == "BLOCKED"

def test_safety_gate_rejects_invalid_insurance_expiry():
    from main import ut_safety_gate
    actor = {"identity_id": "sys", "device_id": "sys", "role": "UT_SAFETY"}
    asset_data = {"capacity": 20, "passenger_count": 10, "captain_status": "VERIFIED", "lifejacket_count": 20, "insurance_expiry": "INVALID-DATE"}
    weather_data = {"sea_state": 1}
    result = ut_safety_gate.validate_dispatch(actor, asset_data, weather_data)
    assert not result["checks"]["insurance_valid"]
    assert result["gate_status"] == "BLOCKED"

def test_safety_gate_accepts_future_valid_insurance():
    from main import ut_safety_gate
    actor = {"identity_id": "sys", "device_id": "sys", "role": "UT_SAFETY"}

    valid_date = (datetime.now(UTC) + timedelta(days=365)).strftime("%Y-%m-%d")
    asset_data = {"capacity": 20, "passenger_count": 10, "captain_status": "VERIFIED", "lifejacket_count": 20, "insurance_expiry": valid_date}
    weather_data = {"sea_state": 1}

    result = ut_safety_gate.validate_dispatch(actor, asset_data, weather_data)
    assert result["checks"]["insurance_valid"]
    assert result["gate_status"] == "APPROVED"

def test_confirm_booking_not_found_returns_404():
    identity_id = "test-actor-1"
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": "dev-1",
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }
    identity_core.profiles[identity_id] = {"profile_type": "B2C_GUEST", "verification_status": "verified"}
    identity_core.devices["dev-1"] = {"identity_id": identity_id}

    response = client.post("/imoxon/ut/bookings/confirm?booking_id=UT-NONEXISTENT", headers=headers)
    assert response.status_code == 404
    assert "BOOKING_NOT_FOUND" in response.json()["detail"]

def test_confirm_booking_invalid_id_returns_400():
    identity_id = "test-actor-1"
    headers = {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": "dev-1",
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }
    identity_core.profiles[identity_id] = {"profile_type": "B2C_GUEST", "verification_status": "verified"}
    identity_core.devices["dev-1"] = {"identity_id": identity_id}

    response = client.post("/imoxon/ut/bookings/confirm?booking_id=MALFORMED", headers=headers)
    assert response.status_code == 400
    assert "INVALID_BOOKING_ID" in response.json()["detail"]
