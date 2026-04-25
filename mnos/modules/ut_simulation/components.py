import random

class ESGSimulator:
    def get_green_score(self, vessel_id: str) -> float:
        # Simulate carbon footprint and eco-rating
        return round(random.uniform(0.6, 0.95), 2)

class DemandGenerator:
    def generate_wave(self, region: str) -> int:
        # Simulate passenger demand waves
        return random.randint(50, 500)

class FuelSimulator:
    def estimate_consumption(self, distance_km: float, vessel_type: str) -> float:
        rate = 0.5 if vessel_type == "speedboat" else 2.5
        return distance_km * rate

esg_sim = ESGSimulator()
demand_gen = DemandGenerator()
fuel_sim = FuelSimulator()
