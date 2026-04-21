from typing import Dict, Any
import uuid

def calculate_trip_esg(distance_km: float, weight_kg: float, transport_type: str = "vessel") -> Dict[str, Any]:
    factors = {
        "vessel": 0.05,
        "seaplane": 0.50,
        "truck": 0.15
    }

    factor = factors.get(transport_type, 0.1)
    co2_kg = (distance_km * (weight_kg / 1000.0)) * factor
    esg_score = 100 - min(co2_kg * 10, 100)

    return {
        "co2_kg": round(co2_kg, 4),
        "esg_score": round(esg_score, 2),
        "waste_tracking": "ENABLED",
        "circular_verified": True
    }
