from typing import Dict, Any

# Maldives-specific rates (Simulated in USD)
RATES = {
    "concrete_per_m3": 250.00,
    "steel_per_ton": 1200.00,
    "blocks_per_sqm": 45.00,
    "finishes_per_sqm": 80.00,
    "high_end_finish_markup": 1.5, # 50% more for luxury rooms
    "labor_markup": 0.35,
    "transport_markup": 0.15
}

def calculate_boq_and_cost(layout: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates quantities and estimates costs based on the generated layout.
    Geometry-Driven Economics v1.0 + Interior Procurement
    """
    if "error" in layout:
        return {"error": f"BOQ Failed: {layout['error']}"}

    floors = layout["floors"]
    usable = layout["footprint"]
    structural = layout["structural"]

    total_columns = structural["columns"]
    total_area_sqft = usable["width"] * usable["depth"] * floors
    total_area_sqm = total_area_sqft * 0.092903

    # 1. Structural Quantities
    footing_count = total_columns
    concrete_volume_m3 = (total_area_sqm * 0.15) + (total_columns * 0.8)
    steel_tonnage = total_columns * 0.6

    # 2. Interior & Furniture Costs (NEW)
    furniture_cost = sum(int_plan["total_interior_cost"] for int_plan in layout.get("interiors", [])) * floors

    # 3. Blockwork & Finishes
    perimeter_ft = 0
    for comp in layout["components"]:
        if comp["type"] == "room":
            perimeter_ft += 2 * (comp["dimensions"]["width"] + comp["dimensions"]["depth"])

    blockwork_area_sqm = (perimeter_ft * 10 * floors) * 0.092903

    # Apply high-end finish markup if requested (simulated check)
    finish_rate = RATES["finishes_per_sqm"] * RATES["high_end_finish_markup"]

    costs = {
        "concrete": concrete_volume_m3 * RATES["concrete_per_m3"],
        "steel": steel_tonnage * RATES["steel_per_ton"],
        "blocks": blockwork_area_sqm * RATES["blocks_per_sqm"],
        "finishes": total_area_sqm * finish_rate,
        "furniture": furniture_cost
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
            "furniture_items_count": len(layout.get("interiors", [])) * 4 * floors, # 4 items per room
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
