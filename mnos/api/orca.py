from fastapi import APIRouter, Depends, HTTPException

def create_orca_router(orca_engine, get_actor_ctx):
    router = APIRouter(prefix="/orca", tags=["orca"])

    @router.post("/validate")
    async def validate_mission(drone_data: dict, incident_data: dict, actor: dict = Depends(get_actor_ctx)):
        """ORCA: Validate mission safety and compliance."""
        return await orca_engine.validate_mission(actor, drone_data, incident_data)

    @router.get("/metrics")
    async def get_metrics(actor: dict = Depends(get_actor_ctx)):
        """ORCA Dashboard: Fetch operational metrics."""
        return orca_engine.get_metrics()

    return router
