from typing import Dict, Any, List
import uuid

def optimize_route(origin: str, destination: str, current_load_kg: float) -> Dict[str, Any]:
    # Simulation: Return trip matching logic
    # If destination has pending cargo back to origin, deadweight is eliminated

    # Mocking a match
    match_found = True
    return_cargo = "Waste Plastic / Recycling" if match_found else None

    return {
        "route_id": f"rt_{uuid.uuid4().hex[:6]}",
        "origin": origin,
        "destination": destination,
        "load_kg": current_load_kg,
        "return_trip_optimized": match_found,
        "return_cargo": return_cargo,
        "efficiency_gain": 0.45 if match_found else 0.0
    }
