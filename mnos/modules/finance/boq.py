from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP

# Maldives-specific rates (Simulated in USD)
RATES = {
    "concrete_per_m3": 250.00,
    "steel_per_ton": 1200.00,
    "blocks_per_sqm": 45.00,
    "finishes_per_sqm": 80.00,
    "labor_markup": 0.35,  # 35% labor cost
    "transport_markup": 0.15 # 15% island transport
}

def calculate_boq_and_cost(layout: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates quantities and estimates costs based on the generated layout.
    """
    floors = layout["floors"]
    footprint_area_sqft = layout["footprint"]["width"] * layout["footprint"]["depth"]
    total_area_sqft = footprint_area_sqft * floors

    # Convert sqft to sqm for standard metric rates used in Maldives
    total_area_sqm = total_area_sqft * 0.092903

    # Simple Quantity Heuristics
    concrete_volume_m3 = total_area_sqm * 0.15  # Avg 150mm slab equiv
    steel_weight_tons = concrete_volume_m3 * 0.12 # 120kg per m3 avg
    blockwork_area_sqm = total_area_sqm * 1.5  # Walls heuristic

    costs = {
        "concrete": concrete_volume_m3 * RATES["concrete_per_m3"],
        "steel": steel_weight_tons * RATES["steel_per_ton"],
        "blocks": blockwork_area_sqm * RATES["blocks_per_sqm"],
        "finishes": total_area_sqm * RATES["finishes_per_sqm"]
    }

    subtotal = sum(costs.values())
    labor_cost = subtotal * RATES["labor_markup"]
    transport_cost = subtotal * RATES["transport_markup"]

    total_estimate = subtotal + labor_cost + transport_cost

    return {
        "quantities": {
            "concrete_m3": round(concrete_volume_m3, 2),
            "steel_tons": round(steel_weight_tons, 2),
            "blockwork_sqm": round(blockwork_area_sqm, 2),
            "total_area_sqm": round(total_area_sqm, 2)
        },
        "costs": {k: round(v, 2) for k, v in costs.items()},
        "logistics": {
            "labor": round(labor_cost, 2),
            "transport": round(transport_cost, 2)
        },
        "total_estimate": round(total_estimate, 2),
        "currency": "USD"
    }
