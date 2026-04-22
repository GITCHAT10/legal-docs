from typing import Dict, Any

RATES = {
    "concrete_per_m3": 250.00,
    "steel_per_ton": 1200.00,
    "labor_markup": 0.35,
    "transport_markup": 0.15,
    "island_mobilization": 15000.00
}

def calculate_boq_and_cost(layout: Dict[str, Any], event_bus=None) -> Dict[str, Any]:
    """
    FINANCIAL CONTROL ENGINE (FCE) - Geometry Driven.
    Emits MNOS EVENTS for construction phases.
    """
    if "error" in layout: return {"error": layout["error"]}

    floors = layout["floors"]
    total_columns = layout["structural"]["columns"]
    total_area_sqm = layout["footprint"]["width"] * layout["footprint"]["depth"] * floors * 0.0929

    # 1. Geometry-Driven Quantities
    concrete_m3 = (total_area_sqm * 0.15) + (total_columns * 0.8)
    steel_tons = total_columns * 0.6

    costs = {
        "structural": (concrete_m3 * RATES["concrete_per_m3"]) + (steel_tons * RATES["steel_per_ton"]),
        "mobilization": RATES["island_mobilization"] * floors,
        "interiors": sum(i["total_interior_cost"] for i in layout["interiors"]) * floors
    }

    subtotal = sum(costs.values())
    total = subtotal * (1 + RATES["labor_markup"] + RATES["transport_markup"])

    # 2. EMIT CONSTRUCTION PHASE EVENTS
    if event_bus:
        event_bus.emit("FCE_COST_LEDGER_UPDATE", {"project_total": round(total, 2), "structural_lock": True})
        event_bus.emit("CONSTRUCTION_PHASE_STARTED", {"phase": "MOBILIZATION", "budget": costs["mobilization"]})

    return {
        "fce_ledger": {
            "total_commitment": round(total, 2),
            "currency": "USD",
            "breakdown": {k: round(v, 2) for k, v in costs.items()}
        },
        "quantities": {
            "steel_tons": round(steel_tons, 2),
            "concrete_m3": round(concrete_m3, 2),
            "footings": total_columns,
            "columns": total_columns
        }
    }
