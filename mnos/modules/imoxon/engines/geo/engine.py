class GeoEngine:
    def __init__(self):
        self.locations = {} # store_id -> (lat, lon)

    def find_nearest_store(self, user_lat: float, user_lon: float):
        return "island_store_001"

    def calculate_delivery_radius(self, store_id: str):
        return 5.0 # km
