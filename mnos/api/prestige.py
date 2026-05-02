from fastapi import APIRouter, Depends

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

    @router.post("/agentic/booking-flow")
    async def run_agentic_flow(data: dict, actor: dict = Depends(get_actor_ctx)):
        # Inject orchestrator from main (mocking dep injection for router factory)
        from main import prestige_orchestrator
        return await prestige_orchestrator.run_booking_flow(data, actor)

    @router.get("/config")
    async def get_config(actor: dict = Depends(get_actor_ctx)):
        from mnos.modules.prestige.config import PRESTIGE_CONFIG
        return PRESTIGE_CONFIG

    return router
