import math
from typing import List, Dict, Any
from mnos.core.ai.parser import BuildingRequest

def generate_layout(request: BuildingRequest, compliance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a 2D layout based on building request and compliance constraints.
    Deterministic Geometry Engine v1.0
    """
    usable = compliance.get("usable_dimensions")
    if not usable or not compliance.get("is_compliant"):
        return {"error": "Non-compliant or invalid dimensions provided."}

    width = usable["width"]
    depth = usable["depth"]

    stair_width = 10
    stair_depth = 10
    corridor_width = 4
    min_room_width = 8

    # Deterministic Guard: Can we even fit a corridor and a room?
    if width < (corridor_width + min_room_width):
        return {"error": "Impossible Geometry: Width too small for room + corridor."}

    # 1. Staircase position (Hard Corner)
    layout = {
        "floors": request.floors,
        "footprint": usable,
        "components": [],
        "structural": {}
    }

    layout["components"].append({
        "type": "staircase",
        "dimensions": {"width": stair_width, "depth": stair_depth},
        "position": {"x": 0, "y": 0}
    })

    # 2. Corridor Logic (Single-loaded for tight plots, double for wide)
    # Double-loaded requires: 2*room + corridor
    is_double_loaded = width >= (2 * min_room_width + corridor_width)

    room_count = request.rooms_per_floor
    if is_double_loaded:
        rows = math.ceil(room_count / 2)
        room_width = (width - corridor_width) / 2
        corridor_x = room_width
    else:
        rows = room_count
        room_width = width - corridor_width
        corridor_x = room_width

    corridor_depth = depth - stair_depth
    if corridor_depth <= 0:
        return {"error": "Impossible Geometry: No depth remaining for rooms."}

    layout["components"].append({
        "type": "corridor",
        "dimensions": {"width": corridor_width, "depth": corridor_depth},
        "position": {"x": corridor_x, "y": stair_depth}
    })

    # 3. Room Placement (Ceiling-based Row Calculation)
    room_depth = corridor_depth / rows

    for i in range(room_count):
        if is_double_loaded:
            side = i % 2
            row = i // 2
            x_pos = 0 if side == 0 else room_width + corridor_width
        else:
            row = i
            x_pos = 0

        layout["components"].append({
            "type": "room",
            "id": f"Room_{i+1}",
            "dimensions": {"width": room_width, "depth": room_depth},
            "position": {"x": x_pos, "y": stair_depth + (row * room_depth)}
        })

    # 4. Structural Grid (Derived Columns)
    col_per_row = 3 if is_double_loaded else 2
    total_columns = (rows + 1) * col_per_row

    layout["structural"] = {
        "columns": total_columns,
        "footings": total_columns, # Simplified grid
        "grid_rows": rows + 1,
        "grid_cols": col_per_row
    }

    if "terrace" in request.features:
        layout["components"].append({
            "type": "terrace",
            "level": "Roof",
            "area": width * depth
        })

    return layout
