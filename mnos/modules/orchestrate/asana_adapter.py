from typing import List, Dict, Any
import uuid

class AsanaTask(BaseModel if 'BaseModel' in globals() else object):
    id: str
    name: str
    role: str
    phase: str
    dependency: str = None

# Compatibility
from pydantic import BaseModel

def auto_generate_asana_board(design_data: Dict[str, Any], boq_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ABEOS + Asana Workflow Engine:
    Auto-generates human-actionable tasks from ABEOS outputs.
    """
    project_id = f"ASANA-{uuid.uuid4().hex[:4].upper()}"

    # 1. Phase Mapping (Construction Lifecycle)
    tasks = [
        # Phase 1: Site Prep
        {"name": "EIA Submission for Omadhoo", "role": "Environmental Consultant", "phase": "P1: Site Prep"},
        {"name": "Site Survey & Boundary Marking", "role": "Surveyor", "phase": "P1: Site Prep"},

        # Phase 2: Foundation (Driven by BOQ)
        {"name": f"Excavate for {boq_data['quantities']['footings']} Footings", "role": "Excavation Team", "phase": "P2: Foundation"},
        {"name": f"Pour {boq_data['quantities']['concrete_m3']}m3 Concrete (Footings)", "role": "Concrete Contractor", "phase": "P2: Foundation"},

        # Phase 3: Structural (Driven by Steel Order)
        {"name": f"Receive {boq_data['quantities']['steel_tons']}T Steel from Alibaba", "role": "Logistics Officer", "phase": "P3: Structural"},
        {"name": "Erect Structural Steel Frame", "role": "Steel Fabricator", "phase": "P3: Structural"},

        # Phase 4: Interiors (Programa Integration)
        {"name": f"Fit-out {len(design_data.get('interiors', []))} Hotel Rooms", "role": "Interior Designer", "phase": "P4: Interiors"},
        {"name": "Install IKEA/Wayfair Furniture Pack", "role": "Setup Crew", "phase": "P4: Interiors"}
    ]

    # Add Task IDs
    for t in tasks:
        t["id"] = str(uuid.uuid4())[:8]

    return {
        "board_name": f"ABEOS Project Execution: {project_id}",
        "sections": ["P1: Site Prep", "P2: Foundation", "P3: Structural", "P4: Interiors"],
        "tasks": tasks,
        "human_layer_status": "READY_FOR_HANDOVER"
    }
