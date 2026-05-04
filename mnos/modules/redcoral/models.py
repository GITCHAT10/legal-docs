from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class DesignBrief(BaseModel):
    project_id: str
    client_id: str
    title: str
    requirements: List[str]
    budget_range: str
    timestamp: datetime = datetime.now()

class StylePackage(BaseModel):
    package_id: str
    project_id: str
    direction_name: str
    color_palette: List[str]
    materials: List[str]
    moodboard_urls: List[str]

class RenderBrief(BaseModel):
    render_id: str
    project_id: str
    views: List[str]
    resolution: str
    lighting_details: str

class VisualApproval(BaseModel):
    approval_id: str
    project_id: str
    approver_id: str
    status: str # APPROVED, REJECTED
    comments: Optional[str] = None
    approval_hash: str

class DesignBaseline(BaseModel):
    project_id: str
    version: str
    specifications: Dict[str, str]
    approved_render_hashes: List[str]
    shadow_event_hash: str

class RedCoralHandoff(BaseModel):
    handoff_id: str
    project_id: str
    design_baseline_id: str
    timestamp: datetime = datetime.now()
    status: str = "PENDING" # PENDING, RECEIVED
