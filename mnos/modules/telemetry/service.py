from mnos.modules.telemetry.schemas import TelemetryPacket, ComfortIndex
from typing import Dict
import math

class StabilityArbiter:
    def __init__(self):
        # Thresholds for Maldives sea state
        self.SMOOTH_THRESHOLD = 2.0
        self.DISCOMFORT_THRESHOLD = 4.0 # Jules alert threshold
        self.ROUGH_THRESHOLD = 7.0
        self.EXTREME_THRESHOLD = 9.0

    def calculate_comfort_index(self, packet: TelemetryPacket) -> ComfortIndex:
        # Simplified formula for demonstration
        # Comfort score 0-10 based on pitch, roll and vibration

        pitch_val = abs(packet.imu.pitch)
        roll_val = abs(packet.imu.roll)
        vib_val = packet.imu.vibration_amplitude

        # Weighted score: 40% Roll, 30% Pitch, 30% Vibration
        score = (roll_val * 0.4) + (pitch_val * 0.3) + (vib_val * 3.0)
        score = min(max(score, 0.0), 10.0)

        status = "SMOOTH"
        recommendation = "Maintain current course."

        if score >= self.EXTREME_THRESHOLD:
            status = "EXTREME"
            recommendation = "IMMEDIATE ACTION REQUIRED: Seek shelter or adjust heading by 45 degrees."
        elif score >= self.ROUGH_THRESHOLD:
            status = "ROUGH"
            recommendation = "Adjust heading 30 degrees to avoid resonant swell."
        elif score >= self.DISCOMFORT_THRESHOLD:
            status = "MODERATE"
            recommendation = "Adjust heading 15 degrees to avoid resonant swell."
        elif score >= self.SMOOTH_THRESHOLD:
            status = "SMOOTH"
            recommendation = "Slightly reduce speed for passenger comfort."

        return ComfortIndex(
            vessel_id=packet.vessel_id,
            score=round(score, 2),
            pitch_stability=round(10.0 - min(pitch_val, 10.0), 2),
            roll_stability=round(10.0 - min(roll_val, 10.0), 2),
            vibration_level=round(vib_val, 2),
            status=status,
            recommendation=recommendation
        )

    def generate_stability_certificate(self, vessel_id: str, historical_scores: list) -> Dict:
        avg_score = sum(historical_scores) / len(historical_scores) if historical_scores else 0
        comfort_rating = round((10.0 - avg_score) * 10, 1) # Convert to 0-100%

        return {
            "vessel_id": vessel_id,
            "certificate_id": f"CERT-{vessel_id}-2024",
            "comfort_rating": f"{comfort_rating}%",
            "jules_verified": comfort_rating >= 90.0,
            "issue_date": "2024-05-20"
        }
