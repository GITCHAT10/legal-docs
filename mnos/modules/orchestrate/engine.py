from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid

class IslandTask(BaseModel if 'BaseModel' in globals() else object):
    id: str
    name: str
    duration_days: int
    dependencies: List[str]
    status: str = "PENDING"
    risk_level: str = "LOW"

# For compatibility since I might not have pydantic imported here if I don't use it
from pydantic import BaseModel

class ProjectTimeline(BaseModel):
    project_id: str
    island_name: str
    milestones: List[Dict[str, Any]]
    total_duration: int
    logistics_ready: bool

def generate_island_timeline(island_name: str, build_complexity: float) -> ProjectTimeline:
    """
    NEXUS ASI Orchestration: Asana-style task management for Island Nations.
    Calculates milestones based on Maldives-specific logistics.
    """
    project_id = f"ASI-PRJ-{uuid.uuid4().hex[:4].upper()}"

    # Island-Specific Milestones
    milestones = [
        {"task": "EIA & EPA Approval (Environmental)", "duration": 45, "critical": True},
        {"task": "Barge Logistics & Route Planning", "duration": 14, "critical": True},
        {"task": "Site Mobilization & Temp Housing", "duration": 21, "critical": False},
        {"task": "Foundation & Footing Phase", "duration": 30 * build_complexity, "critical": True},
        {"task": "Structural Frame (Steel/Concrete)", "duration": 60 * build_complexity, "critical": True},
        {"task": "Finishing & Interior Fit-out", "duration": 45 * build_complexity, "critical": False},
        {"task": "Handover & QC Inspection", "duration": 10, "critical": True}
    ]

    # Weather Guard (Monsoon Logic)
    current_month = datetime.now().month
    is_monsoon = 5 <= current_month <= 10 # SW Monsoon (Hulhangu)

    if is_monsoon:
        for m in milestones:
            if "Barge" in m["task"] or "Structural" in m["task"]:
                m["duration"] *= 1.3 # 30% delay for sea conditions
                m["risk_level"] = "HIGH"

    total_days = sum(m["duration"] for m in milestones)

    return ProjectTimeline(
        project_id=project_id,
        island_name=island_name,
        milestones=milestones,
        total_duration=int(total_days),
        logistics_ready=not is_monsoon
    )
