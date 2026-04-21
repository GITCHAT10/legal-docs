from pydantic import BaseModel, Field
from typing import List, Optional

class Plot(BaseModel):
    width: float = Field(..., description="Width of the plot in feet")
    depth: float = Field(..., description="Depth of the plot in feet")

class BuildingRequest(BaseModel):
    plot: Plot
    floors: int = Field(..., ge=1, description="Number of floors")
    rooms_per_floor: int = Field(..., ge=1, description="Number of rooms per floor")
    building_type: str = Field("hotel", alias="type", description="Type of building (e.g., hotel, residential)")
    features: List[str] = Field(default_factory=list, description="Special features like terrace, pool, etc.")

def parse_prompt_to_request(prompt: str) -> BuildingRequest:
    """
    Simulated AI Parser. In a real scenario, this would call an LLM (like GPT-4)
    to convert natural language into the structured BuildingRequest.
    """
    # Simple heuristic-based simulation for the demo
    if "30x50" in prompt and "3 floors" in prompt:
        return BuildingRequest(
            plot=Plot(width=30, depth=50),
            floors=3,
            rooms_per_floor=5,
            type="hotel",
            features=["terrace"] if "terrace" in prompt.lower() else []
        )

    # Default fallback
    return BuildingRequest(
        plot=Plot(width=30, depth=50),
        floors=1,
        rooms_per_floor=1,
        type="hotel"
    )
