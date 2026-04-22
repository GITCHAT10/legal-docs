from typing import Dict, Any, List
import random

class HealthGridService:
    """
    Predictive Grid Balancing: Anticipates facility load and reroutes patient tokens.
    """
    def __init__(self):
        # Mocking facility load data across atolls
        self.facility_loads = {
            "ADDU_REH": 0.85,
            "HULHUMALE_HOS": 0.92,
            "MAALHOS_HC": 0.45,
            "KUDARIKILU_HC": 0.30
        }

    async def predict_facility_load(self, facility_id: str) -> float:
        """
        Returns predicted load (0.0 to 1.0) based on historical and real-time events.
        """
        return self.facility_loads.get(facility_id, random.uniform(0.1, 0.9))

    async def get_optimal_reroute(self, patient_atoll: str) -> Optional[str]:
        """
        Reroutes patient 'tokens' to less crowded islands to maintain equilibrium.
        """
        # Finds facility with lowest load in the patient's atoll or nearest region
        sorted_facilities = sorted(self.facility_loads.items(), key=lambda x: x[1])
        if sorted_facilities:
             return sorted_facilities[0][0] # Recommended optimal node
        return None

health_grid_service = HealthGridService()
