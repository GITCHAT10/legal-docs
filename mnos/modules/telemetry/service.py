from mnos.modules.telemetry.schemas import TelemetryPacket, ComfortIndex, FlightState
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
        # Improved formula incorporating foiling and sea state

        pitch_val = abs(packet.imu.pitch)
        roll_val = abs(packet.imu.roll)
        vib_val = packet.imu.vibration_amplitude

        # Base score from IMU
        # Weighted score: 40% Roll, 30% Pitch, 30% Vibration
        base_score = (roll_val * 0.4) + (pitch_val * 0.3) + (vib_val * 3.0)

        # Sea State impact: High waves increase discomfort if not foiling optimally
        sea_state_penalty = packet.wave_height * 1.5

        # Foiling benefit: Being in FOILING state should reduce discomfort if flying height > wave height
        foiling_modifier = 1.0
        if packet.flight_state == FlightState.FOILING:
            if packet.flying_height > packet.wave_height:
                foiling_modifier = 0.6 # 40% reduction in perceived motion
            else:
                foiling_modifier = 1.2 # "Wave slapping" penalty if too low

        score = base_score * foiling_modifier + sea_state_penalty
        score = min(max(score, 0.0), 10.0)

        # Efficiency calculation (Oceanflight optimized)
        # Higher if foiling and speed is high relative to power draw (if available)
        efficiency = 0.5
        if packet.flight_state == FlightState.FOILING:
            efficiency = 0.9

        status = "SMOOTH"
        recommendation = "Maintain current flight profile."

        if score >= self.EXTREME_THRESHOLD:
            status = "EXTREME"
            recommendation = "IMMEDIATE ACTION REQUIRED: Transition to Displacement. Seek shelter."
        elif score >= self.ROUGH_THRESHOLD:
            status = "ROUGH"
            recommendation = "Adjust flight height. Increase flap authority."
        elif score >= self.DISCOMFORT_THRESHOLD:
            status = "MODERATE"
            recommendation = "Adjust heading 15 degrees. Optimize foil pitch for resonant swell."
        elif packet.flight_state != FlightState.FOILING and packet.gnss.speed > 18:
             recommendation = "Transition to FOILING state for 40% comfort increase."

        return ComfortIndex(
            vessel_id=packet.vessel_id,
            score=round(score, 2),
            pitch_stability=round(10.0 - min(pitch_val, 10.0), 2),
            roll_stability=round(10.0 - min(roll_val, 10.0), 2),
            vibration_level=round(vib_val, 2),
            flight_efficiency=efficiency,
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
            "verified_technology": "Oceanflight Foiling System",
            "issue_date": "2024-05-20"
        }
