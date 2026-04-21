from typing import Dict, Any

# Maldives-specific rates (Simulated in USD)
RATES = {
    "concrete_per_m3": 250.00,
    "steel_per_ton": 1200.00,
    "blocks_per_sqm": 45.00,
    "finishes_per_sqm": 80.00,
    "labor_markup": 0.35,
    "transport_markup": 0.15
}

def calculate_boq_and_cost(layout: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates quantities and estimates costs based on the generated layout.
    Geometry-Driven Economics v1.0
    """
    if "error" in layout:
        return {"error": f"BOQ Failed: {layout['error']}"}

    floors = layout["floors"]
    usable = layout["footprint"]
    structural = layout["structural"]

    total_columns = structural["columns"]
    total_area_sqft = usable["width"] * usable["depth"] * floors
    total_area_sqm = total_area_sqft * 0.092903

    # 1. Structural Quantities (Geometry-Driven)
    # Footing count derived from column count
    footing_count = total_columns

    # Concrete Volume: Slabs + Beams + Columns
    concrete_volume_m3 = (total_area_sqm * 0.15) + (total_columns * 0.8) # Heuristic including columns/beams

    # Steel Tonnage: CEO Directive (0.6 tons per column approx)
    steel_tonnage = total_columns * 0.6

    # Blockwork: Based on room perimeter + floor count
    room_count = 0
    perimeter_ft = 0
    for comp in layout["components"]:
        if comp["type"] == "room":
            room_count += 1
            perimeter_ft += 2 * (comp["dimensions"]["width"] + comp["dimensions"]["depth"])

    blockwork_area_sqm = (perimeter_ft * 10 * floors) * 0.092903 # 10ft wall height

    costs = {
        "concrete": concrete_volume_m3 * RATES["concrete_per_m3"],
        "steel": steel_tonnage * RATES["steel_per_ton"],
        "blocks": blockwork_area_sqm * RATES["blocks_per_sqm"],
        "finishes": total_area_sqm * RATES["finishes_per_sqm"]
    }

    subtotal = sum(costs.values())
    labor_cost = subtotal * RATES["labor_markup"]
    transport_cost = subtotal * RATES["transport_markup"]

    total_estimate = subtotal + labor_cost + transport_cost

    return {
        "quantities": {
            "columns": total_columns,
            "footings": footing_count,
            "concrete_m3": round(concrete_volume_m3, 2),
            "steel_tons": round(steel_tonnage, 2),
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
