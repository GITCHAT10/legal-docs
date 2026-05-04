from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from mnos.modules.buildx.models import (
    BuildProject, WorkBreakdownStructure, BOQItem, ContractorPackage,
    ProcurementRequest, Milestone, SiteEvidence, VariationOrder, QAQCCheck, HandoverPackage
)
from mnos.shared.execution_guard import ExecutionGuard
from mnos.shared.auth import get_actor_context

def create_buildx_router(guard: ExecutionGuard, shadow, orca, fce):
    router = APIRouter(prefix="/buildx", tags=["BUILDX"])

    # Project States
    VALID_STATES = [
        "DRAFT", "DESIGN_IN_PROGRESS", "VISUALIZATION_IN_PROGRESS", "PENDING_APPROVAL",
        "APPROVED_DESIGN_LOCKED", "ENGINEERING_VALIDATION", "BUILD_PLANNING", "PROCUREMENT_READY",
        "MARINE_WORKS_ACTIVE", "LAND_WORKS_ACTIVE", "FLOATING_WORKS_ACTIVE", "POOL_SYSTEM_ACTIVE",
        "UTILITY_COORDINATION_ACTIVE", "QA_QC_ACTIVE", "SNAGGING", "HANDOVER_PENDING", "HANDOVER_COMPLETE"
    ]

    FAILURE_STATES = [
        "APPROVAL_REJECTED", "DESIGN_DEVIATION", "ENGINEERING_HOLD", "ENVIRONMENTAL_HOLD",
        "PROCUREMENT_HOLD", "PAYMENT_HOLD", "CONTRACTOR_NONCOMPLIANCE", "SAFETY_HOLD",
        "AUDIT_CHAIN_BROKEN", "ZERO_LEAK_FAILED", "ORCA_VALIDATION_FAILED"
    ]

    @router.post("/project")
    async def create_project(project: BuildProject, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "buildx.project.create",
            actor,
            lambda: {"status": "PROJECT_CREATED", "project_id": project.project_id}
        )

    @router.post("/boq")
    async def create_boq(boq: BOQItem, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "buildx.boq.create",
            actor,
            lambda: {"status": "BOQ_ITEM_ADDED", "item_id": boq.item_id}
        )

    @router.post("/contractor-package")
    async def create_contractor_package(pkg: ContractorPackage, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "buildx.contractor.create",
            actor,
            lambda: {"status": "CONTRACTOR_PACKAGE_CREATED", "package_id": pkg.package_id}
        )

    @router.post("/procurement-request")
    async def create_procurement_request(req: ProcurementRequest, actor: dict = Depends(get_actor_context)):
        # REQUIREMENT: No procurement without iMOXON traceability.
        # This is handled by routing the request to iMOXON through the execution guard.
        return guard.execute_sovereign_action(
            "buildx.procurement.request",
            actor,
            lambda: {"status": "PROCUREMENT_REQUESTED", "request_id": req.request_id}
        )

    @router.post("/milestone")
    async def create_milestone(milestone: Milestone, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "buildx.milestone.create",
            actor,
            lambda: {"status": "MILESTONE_CREATED", "milestone_id": milestone.milestone_id}
        )

    @router.post("/site-evidence")
    async def upload_site_evidence(evidence: SiteEvidence, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "buildx.evidence.upload",
            actor,
            lambda: {
                "status": "EVIDENCE_UPLOADED",
                "evidence_id": evidence.evidence_id,
                "shadow_hash": shadow.commit("buildx.site_evidence", actor["identity_id"], evidence.dict())
            }
        )

    @router.post("/variation")
    async def create_variation(vo: VariationOrder, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "buildx.variation.create",
            actor,
            lambda: {"status": "VARIATION_CREATED", "vo_id": vo.vo_id}
        )

    @router.post("/qaqc")
    async def create_qaqc(check: QAQCCheck, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "buildx.qaqc.create",
            actor,
            lambda: {"status": "QAQC_LOGGED", "check_id": check.check_id}
        )

    @router.post("/handover")
    async def initiate_handover(package: HandoverPackage, actor: dict = Depends(get_actor_context)):
        # REQUIREMENT: Full project can move to HANDOVER_COMPLETE only after RC visual match,
        # AX validation, BX QA/QC, SHADOW proof, and FCE settlement status are complete.

        # Check BX QA/QC
        qaqc_passed = any(
            e["event_type"] == "buildx.qaqc.create.completed" and
            e["payload"]["result"]["status"] == "QAQC_LOGGED" and
            (e["payload"]["result"].get("project_id") == package.project_id or e["payload"].get("project_id") == package.project_id)
            for e in shadow.chain
        )
        if not qaqc_passed:
             raise HTTPException(status_code=400, detail="FAIL CLOSED: BX QA/QC must be complete before handover.")

        return guard.execute_sovereign_action(
            "buildx.handover.initiate",
            actor,
            lambda: {"status": "HANDOVER_PENDING", "package_id": package.package_id}
        )

    @router.post("/request-fce-settlement")
    async def request_fce_settlement(milestone_id: str, project_id: str, amount_mvr: float, actor: dict = Depends(get_actor_context)):
        # REQUIREMENT: BX cannot request FCE settlement unless milestone has site evidence and SHADOW proof.
        evidence_found = any(
            e["event_type"] == "buildx.site_evidence" and
            e["payload"]["milestone_id"] == milestone_id and
            e["payload"].get("project_id") == project_id
            for e in shadow.chain
        )
        if not evidence_found:
            raise HTTPException(status_code=400, detail="FAIL CLOSED: Milestone requires site evidence and SHADOW proof before settlement.")

        # REQUIREMENT: ORCA failed validation must block FCE settlement.
        # Filter failed ORCA validations by project_id and milestone_id
        for event in shadow.chain:
            if event["event_type"].startswith("orca.validation.") and not event["payload"].get("passed"):
                # Scope check: Must match project if project is present in failure
                v_payload = event["payload"]
                v_project_id = v_payload.get("project_id")
                v_milestone_id = v_payload.get("milestone_id")

                # Logic: If failure has a project_id, it must match current project_id.
                # If failure has no project_id but has milestone_id, it must match current milestone_id.
                # If it matches current project OR (it has no project and matches current milestone), block.
                if v_project_id:
                    if v_project_id == project_id:
                         raise HTTPException(status_code=400, detail="FAIL CLOSED: ORCA validation failure blocked FCE settlement.")
                elif v_milestone_id:
                    if v_milestone_id == milestone_id:
                         raise HTTPException(status_code=400, detail="FAIL CLOSED: ORCA validation failure blocked FCE settlement.")

        return guard.execute_sovereign_action(
            "buildx.fce.settlement",
            actor,
            lambda: {
                "status": "SETTLEMENT_REQUESTED",
                "milestone_id": milestone_id,
                "amount": amount_mvr,
                "fce_tx": fce.finalize_invoice(amount_mvr, "RESORT_SUPPLY")
            }
        )

    return router
