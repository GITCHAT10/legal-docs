from fastapi import APIRouter, Depends, HTTPException
from mnos.modules.redcoral.models import DesignBrief, StylePackage, RenderBrief, VisualApproval, RedCoralHandoff
from mnos.shared.execution_guard import ExecutionGuard
from mnos.shared.auth import get_actor_context

def create_redcoral_router(guard: ExecutionGuard, shadow, orca, consent):
    router = APIRouter(prefix="/redcoral", tags=["REDCORAL"])

    @router.post("/brief")
    async def create_brief(brief: DesignBrief, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "redcoral.brief.create",
            actor,
            lambda **kwargs: {"status": "BRIEF_CREATED", "project_id": brief.project_id},
            project_id=brief.project_id
        )

    @router.post("/style-package")
    async def create_style_package(pkg: StylePackage, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "redcoral.style.create",
            actor,
            lambda **kwargs: {"status": "STYLE_PACKAGE_CREATED", "package_id": pkg.package_id},
            project_id=pkg.project_id
        )

    @router.post("/render-brief")
    async def create_render_brief(render: RenderBrief, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "redcoral.render.create",
            actor,
            lambda **kwargs: {"status": "RENDER_BRIEF_CREATED", "render_id": render.render_id},
            project_id=render.project_id
        )

    @router.post("/approve-design")
    async def approve_design(approval: VisualApproval, actor: dict = Depends(get_actor_context)):
        # Check ORCA visual deviation placeholder
        orca_result = orca.validate("VISUAL_DEVIATION", actor["identity_id"], {"project_id": approval.project_id})
        if not orca_result["passed"]:
            raise HTTPException(status_code=400, detail=f"ORCA Visual Deviation Check Failed: {orca_result['failure_reasons']}")

        return guard.execute_sovereign_action(
            "redcoral.design.approve",
            actor,
            lambda **kwargs: {
                "status": "APPROVED",
                "approval_id": approval.approval_id,
                "project_id": approval.project_id,
                "shadow_hash": shadow.commit("redcoral.visual_approval", actor["identity_id"], approval.dict(), project_id=approval.project_id)
            },
            project_id=approval.project_id
        )

    @router.get("/design-baseline/{project_id}")
    async def get_design_baseline(project_id: str, actor: dict = Depends(get_actor_context)):
        # Mock retrieval for now
        return {
            "project_id": project_id,
            "version": "1.0",
            "status": "APPROVED_DESIGN_LOCKED"
        }

    @router.post("/handoff-to-buildx")
    async def handoff_to_buildx(handoff: RedCoralHandoff, actor: dict = Depends(get_actor_context)):
        # REQUIREMENT: RC design cannot hand off to BX unless design is approved and SHADOW-logged.
        # We verify by checking if a redcoral.design.approve.completed event exists for this project in shadow.
        approved = any(
            e["event_type"] == "redcoral.design.approve.completed" and
            e["payload"]["result"]["status"] == "APPROVED" and
            e.get("project_id") == handoff.project_id
            for e in shadow.chain
        )
        if not approved:
            raise HTTPException(status_code=400, detail="FAIL CLOSED: Design must be approved before handoff.")

        return guard.execute_sovereign_action(
            "redcoral.handoff.buildx",
            actor,
            lambda **kwargs: {"status": "HANDOFF_COMPLETE", "handoff_id": handoff.handoff_id},
            project_id=handoff.project_id
        )

    return router
