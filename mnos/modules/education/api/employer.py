from fastapi import FastAPI, HTTPException, Depends, Header
from typing import List, Annotated
import os
from mnos.modules.education.models.schemas import JobDemand, SkillVerification, StudentMatch, CertificationRequest
from mnos.modules.shadow.ledger import ShadowLedger
from datetime import datetime, UTC

app = FastAPI(title="MARS-GLOS Employer API", version="1.0.0")

# Initialize SHADOW Ledger
shadow = ShadowLedger()

# AEGIS Authentication via Environment Variables
AEGIS_KEY = os.getenv("AEGIS_SECRET_KEY", "MIG-SECURE-KEY-FALLBACK")

async def get_current_user(x_api_key: Annotated[str | None, Header()] = None):
    if not x_api_key or x_api_key != AEGIS_KEY:
        raise HTTPException(status_code=401, detail="AEGIS Authentication Failed")
    return {"id": "EMP-001", "role": "employer"}

async def employer_only(user: Annotated[dict, Depends(get_current_user)]):
    if user["role"] != "employer":
        raise HTTPException(status_code=403, detail="Role-based access denied")
    return user

# Mock database
job_demands = []
verifications = []
certifications = []

@app.post("/demand", response_model=JobDemand)
async def post_job_demand(demand: JobDemand):
    """
    Sync real-time job demand from global employers.
    """
    job_demands.append(demand)
    return demand

@app.get("/demand", response_model=List[JobDemand])
async def list_job_demands():
    return job_demands

@app.post("/verify-skill", response_model=SkillVerification)
async def verify_student_skill(verification: SkillVerification):
    """
    Verify student skills based on simulation performance.
    Mandatory SHADOW logging for auditability.
    """
    verifications.append(verification)
    shadow.commit("SKILL_VERIFICATION", "SYSTEM_SIMULATOR", verification.model_dump())
    return verification

@app.get("/match/{job_id}", response_model=List[StudentMatch])
async def match_students(job_id: str):
    """
    Match students to specific job demands using predictive performance capital.
    """
    # Placeholder for matching logic
    return [
        StudentMatch(
            student_id="STU-123",
            job_id=job_id,
            match_score=0.95,
            reasoning="Top 5% in high-fidelity tourism simulations.",
            correlation_id="MATCH-CORR-001"
        )
    ]

@app.post("/certify", response_model=CertificationRequest)
async def certify_student(
    request: CertificationRequest,
    user: Annotated[dict, Depends(employer_only)]
):
    """
    Process certification requests via the 'Law of the Button' UI-driven action.
    Requires AEGIS authentication and employer role.
    Mandatory SHADOW logging for auditability.
    """
    # Enforce human-in-the-loop: actor_id in request must match authenticated user
    if request.actor_id != user["id"]:
         raise HTTPException(status_code=403, detail="Actor identity mismatch")

    if request.actor_role != "employer":
        raise HTTPException(status_code=403, detail="Only employers can certify")

    certifications.append(request)
    shadow.commit("STUDENT_CERTIFICATION", user["id"], request.model_dump())
    return request

@app.get("/health")
async def health_check():
    return {"status": "operational", "timestamp": datetime.now(UTC)}
