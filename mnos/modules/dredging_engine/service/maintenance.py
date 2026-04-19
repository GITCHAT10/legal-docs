from ..models.telemetry import DragflowSensor

class PredictiveMaintenance:
    def __init__(self, vibration_threshold: float = 10.0, temp_threshold: float = 80.0):
        self.vibration_threshold = vibration_threshold
        self.temp_threshold = temp_threshold

    def assess_risk(self, sensor_data: DragflowSensor) -> dict:
        risk_score = 0
        reasons = []

        if sensor_data.vibration > self.vibration_threshold:
            risk_score += 40
            reasons.append("High vibration detected")

        if sensor_data.temperature > self.temp_threshold:
            risk_score += 40
            reasons.append("Overheating detected")

        if sensor_data.inclination > 45.0:
            risk_score += 20
            reasons.append("Extreme inclination")

        status = "HEALTHY"
        if risk_score > 70:
            status = "CRITICAL"
        elif risk_score > 30:
            status = "WARNING"

        return {
            "status": status,
            "risk_score": risk_score,
            "reasons": reasons
        }
