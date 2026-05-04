from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

class AirportProject(BaseModel):
    project_id: str
    name: str
    status: str = "AIRPORT_DRAFT"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RunwayDesign(BaseModel):
    design_id: str
    project_id: str
    length_m: float
    width_m: float
    orientation: str

class TaxiwayDesign(BaseModel):
    design_id: str
    project_id: str
    width_m: float

class ApronDesign(BaseModel):
    design_id: str
    project_id: str
    capacity_aircraft: int

class TerminalAirsideInterface(BaseModel):
    interface_id: str
    project_id: str
    gate_count: int

class PavementDesign(BaseModel):
    pavement_id: str
    project_id: str
    pcn: str # Pavement Classification Number
    validated_by_specialist: bool = False

class ObstacleSurfaceReview(BaseModel):
    review_id: str
    project_id: str
    ols_compliant: bool
    issues: List[str] = []

class AirNavigationReview(BaseModel):
    review_id: str
    project_id: str
    navaid_interference_detected: bool
    issues: List[str] = []

class RFFSCategoryReview(BaseModel):
    review_id: str
    project_id: str
    category: int
    validation_status: bool = False

class AviationEngineerCertification(BaseModel):
    cert_id: str
    project_id: str
    engineer_id: str
    timestamp: datetime = datetime.now()

class MCAACompliancePackage(BaseModel):
    package_id: str
    project_id: str
    icao_precheck: bool = False
    mcaa_precheck: bool = False
    ols_review: bool = False
    pavement_review: bool = False
    rffs_review: bool = False
    engineer_certification: bool = False

class AirportValidationResult(BaseModel):
    project_id: str
    passed: bool
    failure_reasons: List[str] = []
