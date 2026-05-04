from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from mnos.shared.execution_guard import ExecutionGuard
from mnos.shared.auth import get_actor_context

class SonarSurvey(BaseModel):
    survey_id: str
    project_id: str
    data_url: str

class DredgePlan(BaseModel):
    plan_id: str
    project_id: str
    target_volume_cbm: float

class BathymetryModel(BaseModel):
    model_id: str
    project_id: str
    mesh_url: str

class DredgeTelemetry(BaseModel):
    telemetry_id: str
    vessel_id: str
    position: dict
    depth: float

class ReclamationVolumeClaim(BaseModel):
    claim_id: str
    project_id: str
    volume_cbm: float

class MarineValidationResult(BaseModel):
    validation_id: str
    passed: bool
    reasons: List[str]

def create_dredge_router(guard: ExecutionGuard, shadow, orca):
    router = APIRouter(prefix="/atollx/dredge", tags=["ATOLLX_DREDGE"])

    @router.post("/survey")
    async def create_survey(survey: SonarSurvey, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.dredge.survey",
            actor,
            lambda **kwargs: {"status": "SURVEY_LOGGED", "survey_id": survey.survey_id}
        )

    @router.post("/plan")
    async def create_plan(plan: DredgePlan, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.dredge.plan",
            actor,
            lambda **kwargs: {"status": "PLAN_CREATED", "plan_id": plan.plan_id}
        )

    @router.post("/telemetry")
    async def log_telemetry(telemetry: DredgeTelemetry, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.dredge.telemetry",
            actor,
            lambda **kwargs: {"status": "TELEMETRY_LOGGED", "telemetry_id": telemetry.telemetry_id}
        )

    @router.post("/validate")
    async def validate_marine(actor: dict = Depends(get_actor_context)):
        return orca.validate("MARINE_WORKS", actor["identity_id"], {})

    @router.post("/volume-claim")
    async def claim_volume(claim: ReclamationVolumeClaim, actor: dict = Depends(get_actor_context)):
        # REQUIREMENT: Dredge volume claim must fail if sonar/bathymetry proof is missing.
        proof_found = any(
            e["event_type"] == "atollx.dredge.survey.completed" and e["payload"]["result"]["status"] == "SURVEY_LOGGED"
            for e in shadow.chain
        )
        if not proof_found:
            raise HTTPException(status_code=400, detail="FAIL CLOSED: Volume claim requires sonar/bathymetry proof.")

        return guard.execute_sovereign_action(
            "atollx.dredge.volume_claim",
            actor,
            lambda **kwargs: {"status": "VOLUME_CLAIMED", "claim_id": claim.claim_id}
        )

    return router
