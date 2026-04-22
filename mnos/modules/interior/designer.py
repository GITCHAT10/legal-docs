from typing import Dict, Any, List

# Simulated Furniture Brand Catalog (IKEA/Wayfair Hybrid)
CATALOG = {
    "hotel_room": [
        {"item": "King Bed", "brand": "IKEA", "dimensions": {"w": 6.5, "d": 7}, "price": 450},
        {"item": "Nightstand", "brand": "Wayfair", "dimensions": {"w": 1.5, "d": 1.5}, "price": 120},
        {"item": "Desk", "brand": "IKEA", "dimensions": {"w": 4, "d": 2}, "price": 200},
        {"item": "Ergonomic Chair", "brand": "Wayfair", "dimensions": {"w": 2, "d": 2}, "price": 350}
    ]
}

def smart_wizard_populate_room(room_id: str, room_type: str, dimensions: Dict[str, float]) -> Dict[str, Any]:
    """
    AI Interior Smart Wizard: Automatically places furniture based on room type.
    """
    furniture = CATALOG.get(room_type, [])
    placements = []

    # Simple placement logic: Center bed, flank with nightstands
    for item in furniture:
        placements.append({
            "id": f"{room_id}_{item['item'].replace(' ', '_')}",
            "item": item["item"],
            "brand": item["brand"],
            "dimensions": item["dimensions"],
            "price": item["price"]
        })

    return {
        "room_id": room_id,
        "type": room_type,
        "render_mode": "4K_SIMULATED",
        "furniture": placements,
        "total_interior_cost": sum(f["price"] for f in placements)
    }

def scan_room_ar(scan_input: str) -> Dict[str, Any]:
    """
    Magicplan Concept: Converts a textual AR scan into a structured room layout.
    """
    # Simulated Scan: "12x15 bedroom"
    if "12x15" in scan_input:
        return {"width": 12, "depth": 15, "type": "hotel_room"}
    return {"width": 10, "depth": 10, "type": "hotel_room"}
