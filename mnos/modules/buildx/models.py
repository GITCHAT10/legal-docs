from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class BuildProject(BaseModel):
    project_id: str
    title: str
    client_id: str
    site_location: str
    status: str = "DRAFT"

class WorkBreakdownStructure(BaseModel):
    wbs_id: str
    project_id: str
    phases: List[Dict[str, str]]

class BOQItem(BaseModel):
    item_id: str
    project_id: str
    description: str
    quantity: float
    unit: str
    estimated_rate: float

class ContractorPackage(BaseModel):
    package_id: str
    project_id: str
    contractor_id: str
    scope_of_work: str
    contract_value_mvr: float

class ProcurementRequest(BaseModel):
    request_id: str
    project_id: str
    items: List[Dict[str, Any]] = []
    total_estimated_value: float

class Milestone(BaseModel):
    milestone_id: str
    project_id: str
    title: str
    due_date: datetime
    payment_percentage: float
    status: str = "PLANNED"

class SiteEvidence(BaseModel):
    evidence_id: str
    milestone_id: str
    project_id: str
    media_urls: List[str]
    description: str
    timestamp: datetime = datetime.now()

class VariationOrder(BaseModel):
    vo_id: str
    project_id: str
    description: str
    cost_impact_mvr: float
    schedule_impact_days: int
    status: str = "PENDING"

class QAQCCheck(BaseModel):
    check_id: str
    project_id: str
    category: str
    passed: bool
    findings: str
    timestamp: datetime = datetime.now()

class HandoverPackage(BaseModel):
    package_id: str
    project_id: str
    as_built_drawings_url: str
    manuals_url: str
    completion_certificate_url: str
    status: str = "PENDING"
