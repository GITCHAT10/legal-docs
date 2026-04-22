import math

class SewerEngine:
    """
    Maldives Infrastructure & Sewer Engine
    Replicates Pipemate/Bentley OpenFlows Sewer logic for Maldives-specific conditions.
    """
    def __init__(self):
        # Maldives specific constants
        self.roughness_coefficient = 0.013  # PVC/HDPE pipes
        self.min_velocity = 0.6  # m/s for self-cleansing
        self.max_velocity = 3.0  # m/s to prevent erosion

    def calculate_pipe_capacity(self, diameter_mm: float, slope: float):
        """
        Manning's Equation for gravity flow.
        """
        radius_m = (diameter_mm / 1000) / 2
        area = math.pi * (radius_m ** 2)
        wetted_perimeter = 2 * math.pi * radius_m
        hydraulic_radius = area / wetted_perimeter

        # Manning's Equation: V = (1/n) * R^(2/3) * S^(1/2)
        velocity = (1 / self.roughness_coefficient) * (hydraulic_radius ** (2/3)) * (slope ** 0.5)
        flow_rate = velocity * area

        return {
            "velocity_ms": velocity,
            "flow_rate_m3s": flow_rate,
            "is_self_cleansing": velocity >= self.min_velocity,
            "is_safe_velocity": velocity <= self.max_velocity
        }

    def design_network(self, nodes: list):
        """
        Simulates network design across flat terrain.
        """
        design_output = []
        for node in nodes:
            # Maldives terrain is very flat, so we need to ensure minimal slope
            slope = node.get("slope", 0.002)
            capacity = self.calculate_pipe_capacity(node["diameter"], slope)
            design_output.append({
                "node_id": node["id"],
                "capacity": capacity,
                "status": "PASS" if capacity["is_self_cleansing"] and capacity["is_safe_velocity"] else "FAIL"
            })
        return design_output

sewer_engine = SewerEngine()
