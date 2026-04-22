from typing import List, Dict, Any
from pydantic import BaseModel
from mnos.core.ai.parser import BuildingRequest

class ComplianceResult(BaseModel):
    is_compliant: bool
    violations: List[str]
    recommendations: List[str]
    far_result: float
    ventilation_compliant: bool

def check_maldives_compliance(request: BuildingRequest) -> Dict[str, Any]:
    """
    REGULATORY-GRADE COMPLIANCE ENGINE: Maldives Sovereign Rules.
    """
    violations = []
    recommendations = []

    plot_area = request.plot.width * request.plot.depth
    usable_width = request.plot.width - 6
    usable_depth = request.plot.depth - 8

    # 1. FAR Logic
    total_floor_area = (usable_width * usable_depth) * request.floors
    far = total_floor_area / plot_area if plot_area > 0 else 0
    if far > 3.0:
        violations.append(f"FAR Violation: {round(far, 2)} exceeds limit of 3.0 for hotels.")

    # 2. Ventilation Ratio (10%)
    room_sqft = (usable_width * usable_depth) / request.rooms_per_floor if request.rooms_per_floor > 0 else 0
    ventilation_compliant = room_sqft > 120
    if not ventilation_compliant:
        violations.append(f"Ventilation Failure: Room size {round(room_sqft)}sqft too small.")

    # 3. Geometric Hard Guards (CEO DIRECTIVE v2)
    # CEO Directive: Usable depth < 12ft (10ft stairs + 2ft landing) is IMPOSSIBLE
    if usable_depth < 12:
        violations.append("Impossible Plot: Usable depth < 12ft (Minimum for stairs + landing).")
    if usable_width < 12:
        violations.append("Impossible Width: Plot too narrow for hotel corridor + room.")

    return {
        "is_compliant": len(violations) == 0,
        "violations": violations,
        "recommendations": recommendations,
        "far_result": round(far, 2),
        "ventilation_compliant": ventilation_compliant,
        "usable_dimensions": {"width": max(0, usable_width), "depth": max(0, usable_depth)}
    }
