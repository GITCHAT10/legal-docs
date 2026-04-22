from typing import List, Dict, Any
from pydantic import BaseModel
from mnos.core.ai.parser import BuildingRequest

class ComplianceResult(BaseModel):
    is_compliant: bool
    violations: List[str]
    recommendations: List[str]

def check_maldives_compliance(request: BuildingRequest) -> Dict[str, Any]:
    """
    STRENGTHENED COMPLIANCE ENGINE: Maldives Sovereign Rules.
    """
    violations = []
    recommendations = []

    # 1. Setbacks
    usable_width = request.plot.width - 6
    usable_depth = request.plot.depth - 8

    # 2. Hard Room Size & Corridor Width Guards
    if request.building_type == "hotel":
        if usable_width < 12: # 8ft room + 4ft corridor
            violations.append("Width Violation: Insufficient for hotel corridor + room.")

    if request.rooms_per_floor > 6 and (usable_width * usable_depth) < 1500:
        recommendations.append("High Density Warning: Stair clearance must be increased.")

    return {
        "is_compliant": len(violations) == 0,
        "violations": violations,
        "recommendations": recommendations,
        "usable_dimensions": {"width": max(0, usable_width), "depth": max(0, usable_depth)}
    }
