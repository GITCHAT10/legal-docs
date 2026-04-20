import pytest
from fastapi.testclient import TestClient
from mnos.modules.telemetry.app import app, sessions
from mnos.modules.telemetry.service import StabilityArbiter
from mnos.modules.telemetry.schemas import TelemetryPacket, IMUData, GNSSData
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

def test_heartbeat():
    session_token = test_handshake()
    response = client.post(f"/heartbeat?session_token={session_token}")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"

def test_telemetry_ingestion_smooth():
    session_token = test_handshake()
    payload = {
        "vessel_id": "SS-042",
        "session_token": session_token,
        "imu": {
            "pitch": 0.5,
            "roll": 0.5,
            "yaw": 180.0,
            "accel_x": 0.0,
            "accel_y": 0.0,
            "accel_z": 1.0,
            "vibration_frequency": 50.0,
            "vibration_amplitude": 0.01
        },
        "gnss": {
            "latitude": 4.1755,
            "longitude": 73.5093,
            "altitude": 0.0,
            "speed": 15.5,
            "course": 90.0,
            "satellites": 12
        },
        "battery_voltage": 12.6,
        "is_charging": False
    }
    response = client.post("/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RECEIVED"
    assert data["comfort_score"] < 4.0
    assert data["recommendation"] is None

def test_comfort_alert_trigger():
    session_token = test_handshake()
    # Payload designed to score >= 4.0
    # roll*0.4 + pitch*0.3 + vib*3.0 = 5*0.4 + 5*0.3 + 0.5*3.0 = 2.0 + 1.5 + 1.5 = 5.0
    payload = {
        "vessel_id": "SS-042",
        "session_token": session_token,
        "imu": {
            "pitch": 5.0,
            "roll": 5.0,
            "yaw": 180.0,
            "accel_x": 0.0,
            "accel_y": 0.0,
            "accel_z": 1.0,
            "vibration_frequency": 50.0,
            "vibration_amplitude": 0.5
        },
        "gnss": {
            "latitude": 4.1755,
            "longitude": 73.5093,
            "altitude": 0.0,
            "speed": 15.5,
            "course": 90.0,
            "satellites": 12
        },
        "battery_voltage": 12.6,
        "is_charging": False
    }
    response = client.post("/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["comfort_score"] >= 4.0
    assert "15 degrees" in data["recommendation"]

def test_shadow_burst_trigger():
    session_token = test_handshake()
    # High G-force payload
    payload = {
        "vessel_id": "SS-042",
        "session_token": session_token,
        "imu": {
            "pitch": 10.0,
            "roll": 25.0,
            "yaw": 180.0,
            "accel_x": 2.0,
            "accel_y": 2.0,
            "accel_z": 2.0, # Total G = sqrt(12) approx 3.46 > 2.5
            "vibration_frequency": 50.0,
            "vibration_amplitude": 0.5
        },
        "gnss": {
            "latitude": 4.1755,
            "longitude": 73.5093,
            "altitude": 0.0,
            "speed": 15.5,
            "course": 90.0,
            "satellites": 12
        },
        "battery_voltage": 12.6,
        "is_charging": False
    }
    response = client.post("/telemetry", json=payload)
    assert response.status_code == 200
    assert response.json()["total_g"] > 2.5

def test_comfort_index_calculation_service():
    arbiter = StabilityArbiter()
    packet = TelemetryPacket(
        vessel_id="SS-042",
        session_token="fake-token",
        imu=IMUData(
            pitch=5.0,
            roll=5.0,
            yaw=0.0,
            accel_x=0.0, accel_y=0.0, accel_z=1.0,
            vibration_frequency=50.0,
            vibration_amplitude=0.5
        ),
        gnss=GNSSData(
            latitude=0.0, longitude=0.0, altitude=0.0, speed=0.0, course=0.0, satellites=0
        ),
        battery_voltage=12.0,
        is_charging=False
    )
    comfort = arbiter.calculate_comfort_index(packet)
    assert comfort.score == 5.0
    assert comfort.status == "MODERATE"
    assert "15 degrees" in comfort.recommendation
