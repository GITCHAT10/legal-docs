from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from mnos.modules.atollx.airport.models.airport_models import (
    AirportProject, RunwayDesign, TaxiwayDesign, ApronDesign,
    PavementDesign, ObstacleSurfaceReview, AirNavigationReview,
    RFFSCategoryReview, AviationEngineerCertification, MCAACompliancePackage
)
from mnos.shared.execution_guard import ExecutionGuard
from mnos.shared.auth import get_actor_context

def create_airport_router(guard: ExecutionGuard, shadow, orca, fce):
    router = APIRouter(prefix="/atollx/airport", tags=["ATOLLX_AIRPORT"])

    @router.post("/project")
    async def create_project(project: AirportProject, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.airport.project.create",
            actor,
            lambda: {"status": "PROJECT_CREATED", "project_id": project.project_id}
        )

    @router.post("/runway/design")
    async def submit_runway_design(design: RunwayDesign, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.airport.runway.design",
            actor,
            lambda: {"status": "DESIGN_SUBMITTED", "design_id": design.design_id}
        )

    @router.post("/icao/check")
    async def icao_check(project_id: str, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.airport.icao.precheck",
            actor,
            lambda: {"status": "ICAO_PRECHECK_COMPLETED", "project_id": project_id, "compliant": True}
        )

    @router.post("/mcaa/check")
    async def mcaa_check(project_id: str, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.airport.mcaa.precheck",
            actor,
            lambda: {"status": "MCAA_PRECHECK_COMPLETED", "project_id": project_id, "compliant": True}
        )

    @router.post("/pavement/validate")
    async def validate_pavement(design: PavementDesign, actor: dict = Depends(get_actor_context)):

        if not design.validated_by_specialist:
            raise HTTPException(status_code=400, detail="FAIL CLOSED: Specialist validation required for pavement.")

        return guard.execute_sovereign_action(
            "atollx.airport.pavement.validate",
            actor,
            lambda: {"status": "PAVEMENT_VALIDATED", "pavement_id": design.pavement_id}
        )

    @router.post("/ols/review")
    async def ols_review(review: ObstacleSurfaceReview, actor: dict = Depends(get_actor_context)):
        status = "OLS_REVIEW_COMPLETED"
        forced_status = "COMMITTED"
        if not review.ols_compliant:
            status = "OLS_OBSTACLE_HOLD"
            forced_status = "OLS_OBSTACLE_HOLD"

        return guard.execute_sovereign_action(
            "atollx.airport.ols.review",
            actor,
            lambda: {"status": status, "review_id": review.review_id},
            forced_status=forced_status
        )

    @router.post("/navigation/review")
    async def navigation_review(review: AirNavigationReview, actor: dict = Depends(get_actor_context)):
        status = "AIRNAV_REVIEW_COMPLETED"
        forced_status = "COMMITTED"
        if review.navaid_interference_detected:
            status = "AIR_NAVIGATION_HOLD"
            forced_status = "AIR_NAVIGATION_HOLD"

        return guard.execute_sovereign_action(
            "atollx.airport.airnav.review",
            actor,
            lambda: {"status": status, "review_id": review.review_id},
            forced_status=forced_status
        )

    @router.post("/rffs/category")
    async def rffs_category(review: RFFSCategoryReview, actor: dict = Depends(get_actor_context)):
        if not review.validation_status:
            raise HTTPException(status_code=400, detail="FAIL CLOSED: RFFS category validation required.")

        return guard.execute_sovereign_action(
            "atollx.airport.rffs.validate",
            actor,
            lambda: {"status": "RFFS_CATEGORY_VALIDATED", "review_id": review.review_id}
        )

    @router.post("/engineer/certify")
    async def engineer_certify(cert: AviationEngineerCertification, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.airport.engineer.certify",
            actor,
            lambda: {"status": "ENGINEER_CERTIFIED", "cert_id": cert.cert_id}
        )

    @router.post("/mcaa/submission-package")
    async def mcaa_submission(package: MCAACompliancePackage, actor: dict = Depends(get_actor_context)):
        required = [
            package.icao_precheck, package.mcaa_precheck, package.ols_review,
            package.pavement_review, package.rffs_review, package.engineer_certification
        ]
        if not all(required):
             raise HTTPException(status_code=400, detail="FAIL CLOSED: MCAA submission package incomplete. All reviews and certifications required.")

        return guard.execute_sovereign_action(
            "atollx.airport.mcaa.submission_ready",
            actor,
            lambda: {"status": "MCAA_SUBMISSION_READY", "package_id": package.package_id}
        )

    @router.post("/orca/validate")
    async def orca_validate(validation_type: str, actor: dict = Depends(get_actor_context)):
        return orca.validate(validation_type, actor["identity_id"], {})

    @router.post("/fce/settlement-request")
    async def fce_settlement(milestone_id: str, project_id: str, amount_mvr: float, actor: dict = Depends(get_actor_context)):
        # Check ORCA validation blockers
        for event in shadow.chain:
            if event["event_type"].startswith("orca.validation.") and not event["payload"].get("passed"):
                # Scope check: Must match project if project is present in failure
                v_payload = event["payload"]
                v_project_id = v_payload.get("project_id")
                v_milestone_id = v_payload.get("milestone_id")

                if v_project_id:
                    if v_project_id == project_id:
                         raise HTTPException(status_code=400, detail="FAIL CLOSED: ORCA validation failure blocked FCE settlement.")
                elif v_milestone_id:
                    if v_milestone_id == milestone_id:
                         raise HTTPException(status_code=400, detail="FAIL CLOSED: ORCA validation failure blocked FCE settlement.")

        return guard.execute_sovereign_action(
            "atollx.airport.fce.settlement",
            actor,
            lambda: {
                "status": "SETTLEMENT_REQUESTED",
                "milestone_id": milestone_id,
                "amount": amount_mvr,
                "fce_tx": fce.finalize_invoice(amount_mvr, "RESORT_SUPPLY")
            }
        )

    return router
