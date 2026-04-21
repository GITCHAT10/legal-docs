from typing import List, Dict, Any
from mnos.core.ai.parser import BuildingRequest

def generate_layout(request: BuildingRequest, compliance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a 2D layout based on building request and compliance constraints.
    """
    usable = compliance.get("usable_dimensions", {"width": request.plot.width - 6, "depth": request.plot.depth - 8})

    # Simple Layout Logic:
    # 1. Place a central corridor (4ft wide)
    # 2. Place rooms on either side
    # 3. Reserve space for stairs (e.g., 10x10)

    layout = {
        "floors": request.floors,
        "footprint": usable,
        "components": []
    }

    # Staircase position
    layout["components"].append({
        "type": "staircase",
        "dimensions": {"width": 10, "depth": 10},
        "position": {"x": 0, "y": 0}
    })

    # Corridor (Central along depth)
    corridor_width = 4
    layout["components"].append({
        "type": "corridor",
        "dimensions": {"width": corridor_width, "depth": usable["depth"] - 10},
        "position": {"x": (usable["width"] / 2) - (corridor_width / 2), "y": 10}
    })

    # Rooms
    room_count = request.rooms_per_floor
    rooms_per_side = room_count // 2
    room_depth = (usable["depth"] - 10) / (rooms_per_side if rooms_per_side > 0 else 1)
    room_width = (usable["width"] - corridor_width) / 2

    for i in range(room_count):
        side = i % 2
        row = i // 2
        layout["components"].append({
            "type": "room",
            "id": f"Room_{i+1}",
            "dimensions": {"width": room_width, "depth": room_depth},
            "position": {
                "x": 0 if side == 0 else (usable["width"] / 2) + (corridor_width / 2),
                "y": 10 + (row * room_depth)
            }
        })

    if "terrace" in request.features:
        layout["components"].append({
            "type": "terrace",
            "level": "Roof",
            "area": usable["width"] * usable["depth"]
        })

    return layout
