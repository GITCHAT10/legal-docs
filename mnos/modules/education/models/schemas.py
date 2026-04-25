from datetime import datetime, UTC
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

class MARSBaseModel(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra='forbid',
        validate_assignment=True
    )

class Skill(MARSBaseModel):
    id: str
    name: str
    category: str

class JobDemand(MARSBaseModel):
    id: str
    employer_id: str
    title: str
    required_skills: List[str]
    location: str
    salary_range: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class SkillVerification(MARSBaseModel):
    student_id: str
    skill_id: str
    verified: bool
    score: float = Field(ge=0.0, le=1.0)
    verified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    verifier_id: str
    correlation_id: str  # Mandated by ExecutionGuard v10.0

    @field_validator('correlation_id')
    @classmethod
    def validate_correlation(cls, v: str) -> str:
        if not re.match(r'^[A-Z0-9_\-]+$', v):
            raise ValueError('Invalid correlation_id format')
        return v

class StudentMatch(MARSBaseModel):
    student_id: str
    job_id: str
    match_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    correlation_id: str # Mandated by ExecutionGuard v10.0

    @field_validator('correlation_id')
    @classmethod
    def validate_correlation(cls, v: str) -> str:
        if not re.match(r'^[A-Z0-9_\-]+$', v):
            raise ValueError('Invalid correlation_id format')
        return v

class Employer(MARSBaseModel):
    id: str
    name: str
    industry: str
    api_key_hash: str

class Student(MARSBaseModel):
    id: str
    name: str
    email: str
    performance_capital: float = Field(default=0.0, ge=0.0, le=1.0)
    mastery_levels: Dict[str, float] = {}
    verified_certifications: List[str] = []

class CertificationRequest(MARSBaseModel):
    """
    Triggers 'Law of the Button' UI-driven critical action.
    """
    student_id: str
    skill_id: str
    evidence_hash: str  # Forensic evidence lock to SHADOW ledger
    actor_id: str  # The human authority approving the certification
    actor_role: str = "employer" # Added for RBAC validation
    correlation_id: str
    forensic_audit_trace: str = Field(default="REQUIRED") # Enforced trace field
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator('correlation_id')
    @classmethod
    def validate_correlation(cls, v: str) -> str:
        if not re.match(r'^[A-Z0-9_\-]+$', v):
            raise ValueError('Invalid correlation_id format')
        return v
