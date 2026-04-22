from decimal import Decimal
from mnos.modules.moats.engine import moats

class BOQEngine:
    """
    FCE BOQ Engine
    Geometry-driven construction costing for the Maldives.
    """
    def __init__(self):
        self.island_mobilization_cost = Decimal("15000.00")
        self.labor_markup = Decimal("1.35")
        self.transport_markup = Decimal("1.15")

    def generate_boq(self, layout: dict, floor_count: int):
        # Material base costs (simulated)
        steel_cost_per_ton = Decimal("1200.00")
        concrete_cost_per_m2 = Decimal("150.00") # simplified

        steel_total = Decimal(str(layout["steel_tonnage_est"])) * steel_cost_per_ton

        # Calculate base material cost
        base_material_cost = steel_total + (Decimal("200") * Decimal(str(floor_count)) * Decimal("100")) # dummy room cost

        # Apply Maldives markups
        cost_with_transport = base_material_cost * self.transport_markup
        cost_with_labor = cost_with_transport * self.labor_markup

        total_construction_cost = cost_with_labor + self.island_mobilization_cost

        # Apply MOATS fiscal logic (simulating a "sale" or "valuation" price)
        # Assuming valuation is cost + 20% margin
        valuation_base = total_construction_cost * Decimal("1.20")

        # For simplicity, treat valuation_base as base_amount for MOATS
        # Pax count and nights set to 1 for BOQ valuation context
        bill = moats.calculate_bill(valuation_base, 1, 1)

        return {
            "construction_cost": float(total_construction_cost),
            "mobilization": float(self.island_mobilization_cost),
            "fiscal_valuation": bill
        }

boq_engine = BOQEngine()
