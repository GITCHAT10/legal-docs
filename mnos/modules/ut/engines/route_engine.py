import uuid
from typing import List, Dict

class UTRouteEngine:
    def __init__(self):
        self.routes = {} # route_id -> data
        self.hubs = ["MALE_AIRPORT", "MALE_CITY", "HULHUMALE", "MAAFUSHI"]

    def search_routes(self, origin: str, destination: str, mode: str = None) -> List[Dict]:
        """
        Searches for direct or mixed-mode routes.
        """
        results = []
        # Mock route discovery
        if origin == "MALE_AIRPORT" and destination == "MAAFUSHI":
            results.append({
                "route_id": "R-101",
                "mode": "SPEEDBOAT",
                "duration_mins": 45,
                "base_fare": 25.0
            })
            results.append({
                "route_id": "R-102",
                "mode": "PUBLIC_FERRY",
                "duration_mins": 90,
                "base_fare": 2.0
            })

        return results

    def calculate_mixed_journey(self, origin: str, destination: str) -> Dict:
        """
        Calculates complex multi-leg journeys (e.g., Domestic Flight + Boat).
        """
        # Logic for mixed-mode consolidation
        journey = {
            "journey_id": str(uuid.uuid4()),
            "legs": [
                {
                    "leg_order": 1,
                    "mode": "DOMESTIC_FLIGHT",
                    "origin": origin,
                    "destination": "GAN_AIRPORT",
                    "buffer_mins": 60
                },
                {
                    "leg_order": 2,
                    "mode": "RESORT_BOAT",
                    "origin": "GAN_AIRPORT",
                    "destination": destination,
                    "buffer_mins": 0
                }
            ],
            "total_duration_estimate": 180
        }
        return journey

    def apply_safety_restrictions(self, route_id: str, weather_state: str) -> bool:
        """
        Blocks routes based on weather (ORCA/SENTINEL integration).
        """
        if weather_state == "STORM" and "SPEEDBOAT" in route_id:
            return False
        return True
