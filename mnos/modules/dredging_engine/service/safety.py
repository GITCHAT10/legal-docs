from ..models.telemetry import FullTelemetry

class SafetyService:
    def __init__(self, max_depth: float = 20.0):
        self.max_depth = max_depth
        self.reef_zones = [
            {"lat_min": 0.0, "lat_max": 0.005, "lon_min": 0.0, "lon_max": 0.005}
        ]

    def verify_operation(self, telemetry: FullTelemetry) -> dict:
        """
        AEGIS verify equivalent: Enforce max depth and reef protection.
        """
        # Check depth
        if telemetry.dredgepack.z_depth > self.max_depth:
            return {"allowed": False, "reason": "MAX_DEPTH_EXCEEDED", "code": "BLOCK"}

        # Check reef protection
        lat = telemetry.seafarer.latitude
        lon = telemetry.seafarer.longitude
        for zone in self.reef_zones:
            if zone["lat_min"] <= lat <= zone["lat_max"] and zone["lon_min"] <= lon <= zone["lon_max"]:
                return {"allowed": False, "reason": "REEF_PROTECTION_ZONE", "code": "BLOCK"}

        # Emergency stop condition (extreme vibration/inclination)
        if telemetry.dragflow.vibration > 15.0 or telemetry.dragflow.inclination > 60.0:
            return {"allowed": False, "reason": "EMERGENCY_STOP_CONDITION", "code": "FAILED"}

        return {"allowed": True, "reason": "OK", "code": "APPROVED"}
