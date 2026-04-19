import pytest
from ..service.safety import SafetyService
from ..models.telemetry import FullTelemetry

def test_safety_depth_block():
    service = SafetyService(max_depth=10.0)
    data = {
        "dragflow": {"vibration": 1.0, "temperature": 20.0, "inclination": 0.0},
        "seafarer": {"latitude": 1.0, "longitude": 1.0, "sedimentation_depth": 1.0},
        "dredgepack": {"precision_x": 0.0, "precision_y": 0.0, "z_depth": 15.0}, # Over max_depth
        "boat_state": {"current_path": [], "fuel_level": 100.0, "passenger_count": 0}
    }
    telemetry = FullTelemetry(**data)
    result = service.verify_operation(telemetry)
    assert result["allowed"] is False
    assert result["reason"] == "MAX_DEPTH_EXCEEDED"

def test_safety_reef_block():
    service = SafetyService()
    data = {
        "dragflow": {"vibration": 1.0, "temperature": 20.0, "inclination": 0.0},
        "seafarer": {"latitude": 0.002, "longitude": 0.002, "sedimentation_depth": 1.0}, # In reef zone
        "dredgepack": {"precision_x": 0.0, "precision_y": 0.0, "z_depth": 5.0},
        "boat_state": {"current_path": [], "fuel_level": 100.0, "passenger_count": 0}
    }
    telemetry = FullTelemetry(**data)
    result = service.verify_operation(telemetry)
    assert result["allowed"] is False
    assert result["reason"] == "REEF_PROTECTION_ZONE"

def test_safety_emergency_stop():
    service = SafetyService()
    data = {
        "dragflow": {"vibration": 20.0, "temperature": 20.0, "inclination": 0.0}, # Extreme vibration
        "seafarer": {"latitude": 1.0, "longitude": 1.0, "sedimentation_depth": 1.0},
        "dredgepack": {"precision_x": 0.0, "precision_y": 0.0, "z_depth": 5.0},
        "boat_state": {"current_path": [], "fuel_level": 100.0, "passenger_count": 0}
    }
    telemetry = FullTelemetry(**data)
    result = service.verify_operation(telemetry)
    assert result["allowed"] is False
    assert result["reason"] == "EMERGENCY_STOP_CONDITION"
