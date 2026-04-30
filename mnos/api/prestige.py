from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from mnos.modules.prestige.outreach.engine import OutreachEngine
from mnos.modules.prestige.workflows.luxury_package import LuxuryPackageWorkflow

def create_prestige_router(prestige_core, registry, outreach_engine, luxury_workflow, get_actor_ctx):
    router = APIRouter(tags=["prestige"])

    @router.post("/outreach/process")
    async def process_outreach(data: dict, actor: dict = Depends(get_actor_ctx)):
        return await outreach_engine.process_outreach(actor, data)

    @router.post("/outreach/approve")
    async def approve_outreach(data: dict, actor: dict = Depends(get_actor_ctx)):
        return await outreach_engine.approve_and_send(
            actor,
            data.get("approval_id"),
            actor.get("identity_id")
        )

    @router.post("/workflow/luxury-package")
    async def luxury_package_inquiry(data: dict, actor: dict = Depends(get_actor_ctx)):
        return await luxury_workflow.execute_inquiry(actor, data)

    @router.get("/config")
    async def get_config(actor: dict = Depends(get_actor_ctx)):
        from mnos.modules.prestige.config import PRESTIGE_CONFIG
        return PRESTIGE_CONFIG

    return router
