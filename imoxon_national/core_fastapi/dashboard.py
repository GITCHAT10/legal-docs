class MinistryDashboard:
    """
    iMOXON Ministry Dashboard: Real-time national economic visibility.
    """
    def __init__(self, core_api):
        self.core = core_api

    def get_national_status(self):
        return {
            "gdp_flow": "LIVE",
            "inflation": "3.2%",
            "fish_supply": "STABLE",
            "food_index": "RISING"
        }

    def get_island_heatmap(self):
        return [
            {"island": "Male'", "status": "GREEN", "activity": "HIGH"},
            {"island": "Gaafu Alif", "status": "YELLOW", "activity": "SUPPLY_PRESSURE"},
            {"island": "Addu City", "status": "GREEN", "activity": "STABLE"}
        ]

    def get_alerts(self):
        return [
            {"type": "PRICE_WARNING", "item": "Rice", "islands": ["Male", "Gaafu"]},
            {"type": "SHORTAGE_PREDICTION", "item": "Tuna", "eta": "48h"}
        ]
