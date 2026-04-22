import math
from typing import List, Dict, Any
from mnos.core.ai.parser import BuildingRequest
from mnos.modules.interior.designer import smart_wizard_populate_room
from mnos.modules.euper.engine import configure_euper_ai
from mnos.modules.layout.validator import pre_layout_validation, LayoutValidationError

def generate_layout(request: BuildingRequest, compliance: Dict[str, Any]) -> Dict[str, Any]:
    """
    HARDENED DETERMINISTIC LAYOUT ENGINE (ABEOS Core)
    """
    usable = compliance.get("usable_dimensions")

    # 1. PRE-LAYOUT VALIDATION (FAIL FAST)
    try:
        pre_layout_validation(request, usable)
    except LayoutValidationError as e:
        return {"error": str(e), "status": "FAIL_CLOSED"}

    width, depth = usable["width"], usable["depth"]
    stair_width, stair_depth, corridor_width, min_room_width = 10, 10, 4, 8

    layout = {
        "floors": request.floors,
        "footprint": usable,
        "components": [],
        "structural": {},
        "interiors": [],
        "mars_hardware": [],
        "inn_inventory": [] # MNOS INN Compatibility
    }

    # 2. Staircase (Hard Boundary 0,0)
    layout["components"].append({"type": "staircase", "dimensions": {"width": stair_width, "depth": stair_depth}, "position": {"x": 0, "y": 0}})

    # 3. Room Distribution (CEILING BASED - CEO PRIORITY 1)
    is_double_loaded = width >= (2 * min_room_width + corridor_width)
    room_count = request.rooms_per_floor
    rows = math.ceil(room_count / 2) if is_double_loaded else room_count

    room_width = (width - corridor_width) / 2 if is_double_loaded else width - corridor_width
    corridor_depth = depth - stair_depth
    room_depth = corridor_depth / rows

    # Boundary Guard: Ensure no room exceeds plot depth
    for i in range(room_count):
        side, row = (i % 2, i // 2) if is_double_loaded else (0, i)
        x_pos = 0 if side == 0 else room_width + corridor_width
        y_pos = stair_depth + (row * room_depth)

        room_id = f"Room_{i+1}"
        room_dims = {"width": room_width, "depth": room_depth}

        # INN ROOM SCHEMA (MNOS Compatibility)
        layout["inn_inventory"].append({
            "room_id": room_id,
            "status": "VACANT",
            "type": "Standard",
            "sqm": round(room_width * room_depth * 0.0929, 2)
        })

        layout["components"].append({"type": "room", "id": room_id, "dimensions": room_dims, "position": {"x": x_pos, "y": y_pos}})
        layout["interiors"].append(smart_wizard_populate_room(room_id, "hotel_room", room_dims))

        # MARS Hardware allocation
        layout["mars_hardware"].append({"type": "MARS_EDGE_HUB", "location": room_id})

    # 4. Corridor
    layout["components"].append({
        "type": "corridor",
        "dimensions": {"width": corridor_width, "depth": corridor_depth},
        "position": {"x": room_width if is_double_loaded else room_width, "y": stair_depth}
    })

    # 5. Structural & EUPER
    col_per_row = 3 if is_double_loaded else 2
    layout["structural"] = {"columns": (rows + 1) * col_per_row, "footings": (rows + 1) * col_per_row}

    terrace_area = (width * depth) if "terrace" in request.features else 0
    euper_config = configure_euper_ai(width * depth * request.floors, room_count * request.floors, terrace_area)
    layout["euper_config"] = euper_config.model_dump()

    return layout
