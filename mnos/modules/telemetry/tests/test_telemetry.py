import pytest
from fastapi.testclient import TestClient
from mnos.modules.telemetry.app import app, sessions
from mnos.modules.telemetry.service import StabilityArbiter
from mnos.modules.telemetry.schemas import TelemetryPacket, IMUData, GNSSData, FlightState
import uuid

client = TestClient(app)

def test_handshake():
    response = client.post(
        "/handshake",
        json={
            "vessel_id": "SS-042",
            "kit_serial": "KIT-V1-999",
            "firmware_version": "1.0.0"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_token" in data
    assert data["status"] == "CONNECTED"
    return data["session_token"]

def test_telemetry_foiling_smooth():
    session_token = test_handshake()
    payload = {
        "vessel_id": "SS-042",
        "session_token": session_token,
        "flight_state": "FOILING",
        "flying_height": 1.2,
        "wave_height": 0.5,
        "imu": {
            "pitch": 0.5, "roll": 0.5, "yaw": 180.0,
            "accel_x": 0.0, "accel_y": 0.0, "accel_z": 1.0,
            "vibration_frequency": 50.0, "vibration_amplitude": 0.01
        },
        "gnss": {
            "latitude": 4.1755, "longitude": 73.5093, "altitude": 0.0,
            "speed": 25.5, "course": 90.0, "satellites": 12
        },
        "battery_voltage": 12.6, "is_charging": False
    }
    response = client.post("/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["flight_state"] == "FOILING"
    # Comfort score should be low because flying_height > wave_height
    assert data["comfort_score"] < 4.0

def test_telemetry_foiling_rough_wave_slap():
    session_token = test_handshake()
    payload = {
        "vessel_id": "SS-042",
        "session_token": session_token,
        "flight_state": "FOILING",
        "flying_height": 0.4,
        "wave_height": 0.5, # flying_height < wave_height -> Wave slap
        "imu": {
            "pitch": 2.0, "roll": 3.0, "yaw": 180.0,
            "accel_x": 0.0, "accel_y": 0.0, "accel_z": 1.0,
            "vibration_frequency": 50.0, "vibration_amplitude": 0.1
        },
        "gnss": {
            "latitude": 4.1755, "longitude": 73.5093, "altitude": 0.0,
            "speed": 25.5, "course": 90.0, "satellites": 12
        },
        "battery_voltage": 12.6, "is_charging": False
    }
    response = client.post("/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    # base_score = 3.0*0.4 + 2.0*0.3 + 0.1*3.0 = 1.2 + 0.6 + 0.3 = 2.1
    # slap_penalty = 1.2 * 2.1 = 2.52
    # sea_state_penalty = 0.5 * 1.5 = 0.75
    # score = 3.27
    assert data["comfort_score"] > 3.0

def test_recommendation_transition():
    session_token = test_handshake()
    payload = {
        "vessel_id": "SS-042",
        "session_token": session_token,
        "flight_state": "DISPLACEMENT",
        "imu": {
            "pitch": 0.5, "roll": 0.5, "yaw": 180.0,
            "accel_x": 0.0, "accel_y": 0.0, "accel_z": 1.0,
            "vibration_frequency": 50.0, "vibration_amplitude": 0.01
        },
        "gnss": {
            "latitude": 4.1755, "longitude": 73.5093, "altitude": 0.0,
            "speed": 20.0, # High speed in displacement
            "course": 90.0, "satellites": 12
        },
        "battery_voltage": 12.6, "is_charging": False
    }
    response = client.post("/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Transition to FOILING" in data["recommendation"]

def test_shadow_burst_trigger():
    session_token = test_handshake()
    payload = {
        "vessel_id": "SS-042",
        "session_token": session_token,
        "imu": {
            "pitch": 10.0, "roll": 25.0, "yaw": 180.0,
            "accel_x": 2.0, "accel_y": 2.0, "accel_z": 2.0,
            "vibration_frequency": 50.0, "vibration_amplitude": 0.5
        },
        "gnss": {
            "latitude": 4.1755, "longitude": 73.5093, "altitude": 0.0,
            "speed": 15.5, "course": 90.0, "satellites": 12
        },
        "battery_voltage": 12.6, "is_charging": False
    }
    response = client.post("/telemetry", json=payload)
    assert response.status_code == 200
    assert response.json()["total_g"] > 2.5
