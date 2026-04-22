from typing import List, Dict, Any
from pydantic import BaseModel
import uuid

class AsanaTask(BaseModel):
    id: str
    name: str
    role: str
    phase: str

def auto_generate_asana_board(design_data: Dict[str, Any], boq_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ABEOS + Asana Workflow Engine.
    """
    project_id = f"ASANA-{uuid.uuid4().hex[:4].upper()}"

    ledger = boq_data.get("fce_ledger", {})
    quantities = boq_data.get("quantities", {})

    tasks = [
        {"name": "EIA Submission for Omadhoo", "role": "Environmental Consultant", "phase": "P1: Site Prep"},
        {"name": f"Excavate for {quantities.get('footings', 0)} Footings", "role": "Excavation Team", "phase": "P2: Foundation"},
        {"name": f"Receive {quantities.get('steel_tons', 0)}T Steel from Alibaba", "role": "Logistics Officer", "phase": "P3: Structural"},
        {"name": f"Fit-out {len(design_data.get('interiors', []))} Hotel Rooms", "role": "Interior Designer", "phase": "P4: Interiors"}
    ]

    for t in tasks: t["id"] = str(uuid.uuid4())[:8]

    return {
        "board_name": f"ABEOS Project Execution: {project_id}",
        "tasks": tasks
    }
