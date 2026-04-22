from typing import Dict, Any

# Maldives-specific rates (Simulated in USD)
RATES = {
    "concrete_per_m3": 250.00,
    "steel_per_ton": 1200.00,
    "blocks_per_sqm": 45.00,
    "finishes_per_sqm": 80.00,
    "high_end_finish_markup": 1.5,
    "labor_markup": 0.35,
    "transport_markup": 0.15,
    "island_mobilization_base": 15000.00,
    "mars_iot_unit_cost": 1200.00,
    "mars_recon_unit_cost": 850.00
}

def calculate_boq_and_cost(layout: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates quantities and estimates costs.
    Geometry-Driven Economics v1.0 + Interior + MARS NEXTGEN
    """
    if "error" in layout: return {"error": f"BOQ Failed: {layout['error']}"}

    floors = layout["floors"]
    usable = layout["footprint"]
    structural = layout["structural"]

    total_columns = structural["columns"]
    total_area_sqm = usable["width"] * usable["depth"] * floors * 0.092903

    # 1. Structural
    footing_count = total_columns
    concrete_volume_m3 = (total_area_sqm * 0.15) + (total_columns * 0.8)
    steel_tonnage = total_columns * 0.6

    # 2. Interior
    furniture_cost = sum(int_plan["total_interior_cost"] for int_plan in layout.get("interiors", [])) * floors

    # 3. MARS NEXTGEN HARDWARE
    mars_iot_count = sum(1 for h in layout["mars_hardware"] if "EDGE_HUB" in h["type"])
    mars_recon_count = sum(1 for h in layout["mars_hardware"] if "RECON" in h["type"])
    mars_hardware_cost = (mars_iot_count * RATES["mars_iot_unit_cost"]) + (mars_recon_count * RATES["mars_recon_unit_cost"])

    # 4. Logistics
    mobilization_cost = RATES["island_mobilization_base"] * (1 + (floors * 0.2))

    costs = {
        "concrete": concrete_volume_m3 * RATES["concrete_per_m3"],
        "steel": steel_tonnage * RATES["steel_per_ton"],
        "finishes": total_area_sqm * RATES["finishes_per_sqm"] * RATES["high_end_finish_markup"],
        "furniture": furniture_cost,
        "mars_systems": mars_hardware_cost,
        "mobilization": mobilization_cost
    }

    subtotal = sum(costs.values())
    total_estimate = subtotal * (1 + RATES["labor_markup"] + RATES["transport_markup"])

    return {
        "quantities": {
            "columns": total_columns,
            "footings": footing_count,
            "steel_tons": round(steel_tonnage, 2),
            "mars_units": mars_iot_count + mars_recon_count,
            "total_area_sqm": round(total_area_sqm, 2),
            "concrete_m3": round(concrete_volume_m3, 2)
        },
        "costs": {k: round(v, 2) for k, v in costs.items()},
        "total_estimate": round(total_estimate, 2),
        "currency": "USD"
    }
