from typing import List, Dict, Any
from pydantic import BaseModel
from mnos.core.ai.parser import BuildingRequest

class ComplianceResult(BaseModel):
    is_compliant: bool
    violations: List[str]
    recommendations: List[str]

def check_maldives_compliance(request: BuildingRequest) -> Dict[str, Any]:
    """
    Checks the building request against Maldives Building Code and Geometric Feasibility.
    """
    violations = []
    recommendations = []

    # 1. Setbacks (Maldives standard for inhabited islands)
    usable_width = request.plot.width - 6  # 3ft each side
    usable_depth = request.plot.depth - 8  # 5ft front (road), 3ft back

    if usable_width <= 0 or usable_depth <= 0:
        violations.append("Plot size too small for mandatory Maldives setbacks.")

    # 2. Hard Geometric Guard (CEO BLOCKER 2)
    # 10ft for stairs + 2ft minimum landing = 12ft
    if usable_depth > 0 and usable_depth < 12:
        violations.append("Impossible Geometry: Usable depth < 12ft (Minimum for stairs + landing).")

    # 3. Room Comfort Thresholds
    if request.building_type == "hotel":
        recommendations.append("Ensure main staircase is at least 4ft wide per Maldives Fire Safety standards.")

        # 30x50 plot with 5 rooms
        if usable_depth > 0 and usable_width > 0:
            usable_sqft = usable_width * usable_depth
            if (usable_sqft / request.rooms_per_floor) < 150:
                recommendations.append("Extremely high density. Room size may fall below hospitality standards.")

    return {
        "is_compliant": len(violations) == 0,
        "violations": violations,
        "recommendations": recommendations,
        "usable_dimensions": {"width": max(0, usable_width), "depth": max(0, usable_depth)}
    }
