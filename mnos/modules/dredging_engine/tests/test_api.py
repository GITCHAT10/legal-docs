import pytest
from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"
    assert response.json()["module"] == "dredging_engine"
    assert response.json()["compliance"] == "MNOS.SHADOW"

def test_telemetry_ingestion():
    telemetry_data = {
        "dragflow": {"vibration": 5.0, "temperature": 40.0, "inclination": 10.0, "data_source": "REAL"},
        "seafarer": {"latitude": 1.23, "longitude": 4.56, "sedimentation_depth": 2.0},
        "dredgepack": {"precision_x": 0.001, "precision_y": 0.002, "z_depth": 5.0},
        "boat_state": {
            "current_path": [{"lat": 1.23, "lon": 4.56}],
            "fuel_level": 80.0,
            "passenger_count": 20,
            "trace_id": "test_trace_boat"
        },
        "trace_id": "test_trace_123"
    }
    response = client.post("/telemetry", json=telemetry_data)
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    assert "maintenance" in response.json()
    assert "digital_twin" in response.json()
    assert "shadow_id" in response.json()
    assert "fce_ledger" in response.json()

def test_optimize_endpoint():
    boat_state = {
        "current_path": [{"lat": 1.23, "lon": 4.56}, {"lat": 1.24, "lon": 4.57}],
        "fuel_level": 80.0,
        "passenger_count": 20,
        "trace_id": "test_trace_opt"
    }
    response = client.post("/optimize", json=boat_state)
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    assert "optimized_path" in response.json()
    assert "shadow_id" in response.json()
