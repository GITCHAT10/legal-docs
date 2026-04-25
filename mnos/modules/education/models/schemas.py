from datetime import datetime, UTC
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class Skill(BaseModel):
    id: str
    name: str
    category: str

class JobDemand(BaseModel):
    id: str
    employer_id: str
    title: str
    required_skills: List[str]
    location: str
    salary_range: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class SkillVerification(BaseModel):
    student_id: str
    skill_id: str
    verified: bool
    score: float
    verified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    verifier_id: str
    correlation_id: str  # Mandated by ExecutionGuard v10.0

class StudentMatch(BaseModel):
    student_id: str
    job_id: str
    match_score: float
    reasoning: str
    correlation_id: str # Mandated by ExecutionGuard v10.0

class Employer(BaseModel):
    id: str
    name: str
    industry: str
    api_key_hash: str

class Student(BaseModel):
    id: str
    name: str
    email: str
    performance_capital: float = 0.0
    mastery_levels: Dict[str, float] = {}
    verified_certifications: List[str] = []

class CertificationRequest(BaseModel):
    """
    Triggers 'Law of the Button' UI-driven critical action.
    """
    student_id: str
    skill_id: str
    evidence_hash: str  # Forensic evidence lock to SHADOW ledger
    actor_id: str  # The human authority approving the certification
    correlation_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
