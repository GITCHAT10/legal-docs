from typing import List, Dict, Any
from pydantic import BaseModel
from mnos.core.ai.parser import BuildingRequest

class ComplianceResult(BaseModel):
    is_compliant: bool
    violations: List[str]
    recommendations: List[str]

def check_maldives_compliance(request: BuildingRequest) -> Dict[str, Any]:
    """
    Checks the building request against Maldives Building Code (simulated).
    Rules for inhabited islands (Male', etc.):
    - Setbacks: Usually 5ft from road, 3ft from neighbors (simplified).
    - Max Height: Depends on island, but generally floors x height.
    - Stair Width: Min 3ft for residential, 4ft for public/hotels.
    """
    violations = []
    recommendations = []

    # 1. Setback check (simplified)
    # 30x50 plot is tight.
    usable_width = request.plot.width - 6  # 3ft each side
    usable_depth = request.plot.depth - 8  # 5ft front, 3ft back

    if usable_width <= 0 or usable_depth <= 0:
        violations.append("Plot size too small for mandatory setbacks.")

    # 2. Stair Width Check
    if request.building_type == "hotel":
        recommendations.append("Ensure main staircase is at least 4ft wide per Maldives Fire Safety standards.")

    # 3. Room Count / Ventilation
    # 5 rooms on a 30x50 floor (approx 1500 sqft)
    # Minus setbacks: 24x42 = 1008 sqft usable
    # 1008 / 5 = 200 sqft per room (including corridor). This is tight.
    if request.rooms_per_floor > 4 and request.plot.width * request.plot.depth < 2000:
        recommendations.append("High room density detected. Verify natural ventilation for all bathrooms.")

    return {
        "is_compliant": len(violations) == 0,
        "violations": violations,
        "recommendations": recommendations,
        "usable_dimensions": {"width": usable_width, "depth": usable_depth}
    }
