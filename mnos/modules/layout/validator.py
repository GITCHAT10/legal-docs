from typing import Dict, Any, List
from mnos.core.ai.parser import BuildingRequest

class LayoutValidationError(Exception):
    pass

def pre_layout_validation(request: BuildingRequest, usable: Dict[str, float]):
    """
    PRE-LAYOUT VALIDATION ENGINE: Run BEFORE layout generation.
    Deterministic guards to prevent 'impossible hotels'.
    """
    width = usable.get("width", 0)
    depth = usable.get("depth", 0)

    # 1. Depth Guard (CEO DIRECTIVE v2)
    # CEO Directive: Usable depth < 12ft (10ft stairs + 2ft landing) is IMPOSSIBLE
    if depth < 12:
        raise LayoutValidationError(f"Impossible Depth: Usable depth {depth}ft < 12ft guard.")

    # 2. Width Guard (Room + Corridor minimums)
    min_corridor = 4.0
    min_room_width = 8.0
    if width < (min_corridor + min_room_width):
        raise LayoutValidationError(f"Impossible Width: {width}ft too narrow for room + corridor.")

    # 3. Global Negative Dimension Prevention
    if width <= 0 or depth <= 0:
        raise LayoutValidationError("Geometry Error: Negative or zero usable dimensions.")

    return True
