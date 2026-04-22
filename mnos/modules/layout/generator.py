import math
from typing import List, Dict, Any
from mnos.core.ai.parser import BuildingRequest
from mnos.modules.interior.designer import smart_wizard_populate_room
from mnos.modules.euper.engine import configure_euper_ai

def generate_layout(request: BuildingRequest, compliance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a 2D layout based on building request and compliance constraints.
    Sovereign Core (MNOS) + Execution Layer (MARS NEXTGEN)
    """
    usable = compliance.get("usable_dimensions")
    if not usable or not compliance.get("is_compliant"):
        return {"error": "Non-compliant or invalid dimensions provided."}

    width, depth = usable["width"], usable["depth"]
    stair_width, stair_depth, corridor_width, min_room_width = 10, 10, 4, 8

    layout = {
        "floors": request.floors,
        "footprint": usable,
        "components": [],
        "structural": {},
        "interiors": [],
        "mars_hardware": [] # Unified hardware allocation
    }

    layout["components"].append({"type": "staircase", "dimensions": {"width": stair_width, "depth": stair_depth}, "position": {"x": 0, "y": 0}})

    is_double_loaded = width >= (2 * min_room_width + corridor_width)
    room_count = request.rooms_per_floor
    rows = math.ceil(room_count / 2) if is_double_loaded else room_count
    room_width = (width - corridor_width) / 2 if is_double_loaded else width - corridor_width
    corridor_x = room_width
    corridor_depth = depth - stair_depth

    if corridor_depth <= 0: return {"error": "Impossible Geometry: No depth remaining for rooms."}
    layout["components"].append({"type": "corridor", "dimensions": {"width": corridor_width, "depth": corridor_depth}, "position": {"x": corridor_x, "y": stair_depth}})

    # 2. Rooms + Interiors + MARS Allocation
    room_depth = corridor_depth / rows
    for i in range(room_count):
        side, row = (i % 2, i // 2) if is_double_loaded else (0, i)
        x_pos = 0 if side == 0 else room_width + corridor_width
        room_id = f"Room_{i+1}"
        room_dims = {"width": room_width, "depth": room_depth}
        layout["components"].append({"type": "room", "id": room_id, "dimensions": room_dims, "position": {"x": x_pos, "y": stair_depth + (row * room_depth)}})

        layout["interiors"].append(smart_wizard_populate_room(room_id, "hotel_room", room_dims))

        # ALLOCATE MARS NEXTGEN HARDWARE
        layout["mars_hardware"].append({"type": "MARS_EDGE_HUB", "location": room_id, "protocol": "MATTER"})
        layout["mars_hardware"].append({"type": "MARS_RECON_CAMERA", "location": f"{room_id}_balcony", "protocol": "MQTT"})
        layout["mars_hardware"].append({"type": "MARS_COMMAND_PANEL", "location": f"{room_id}_entry", "protocol": "MATTER"})

    # 3. MARS RECON CORE (Per Floor Lobby)
    for f in range(request.floors):
        layout["mars_hardware"].append({"type": "MARS_RECON_CORE", "location": f"Floor_{f+1}_Lobby"})

    # 4. Structural Grid
    col_per_row = 3 if is_double_loaded else 2
    total_columns = (rows + 1) * col_per_row
    layout["structural"] = {"columns": total_columns, "footings": total_columns}

    # 5. EUPER ENERGY CORE
    terrace_area = (width * depth) if "terrace" in request.features else 0
    euper_config = configure_euper_ai(width * depth * request.floors, room_count * request.floors, terrace_area)
    layout["euper_config"] = euper_config.model_dump()

    if "terrace" in request.features:
        layout["components"].append({"type": "terrace", "level": "Roof", "area": width * depth})

    return layout
