class GISEngine:
    """
    Maldives GIS Engine
    Spatial analytics for Maldives islands and bathymetry.
    Replicates Esri-grade mapping capabilities.
    """
    def __init__(self):
        # Simulated Maldives spatial data
        self.islands = {
            "Male": {"lat": 4.1755, "lon": 73.5093, "type": "Capital"},
            "Hulhumale": {"lat": 4.2188, "lon": 73.5444, "type": "Urban"},
            "Maafushi": {"lat": 3.9444, "lon": 73.4889, "type": "Local Tourism"}
        }

    def get_island_data(self, name: str):
        return self.islands.get(name, {"error": "Island not found"})

    def calculate_setback(self, coastal_line_dist: float):
        """
        Determines building setback requirements based on proximity to sea.
        """
        if coastal_line_dist < 5.0:
            return "FORBIDDEN"
        elif coastal_line_dist < 20.0:
            return "RESTRICTED (Elevated only)"
        else:
            return "PERMITTED"

gis_engine = GISEngine()
