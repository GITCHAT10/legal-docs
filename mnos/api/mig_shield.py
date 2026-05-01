from fastapi import APIRouter, Depends, HTTPException, Header

def create_mig_shield_router(mig_shield_engine, get_actor_ctx):
    router = APIRouter(prefix="/mig-shield", tags=["mig-shield"])

    @router.post("/mission/dispatch")
    async def dispatch_mission(
        data: dict,
        actor: dict = Depends(get_actor_ctx),
        x_aegis_identity: str = Header(None, alias="X-AEGIS-IDENTITY"),
        x_aegis_device: str = Header(None, alias="X-AEGIS-DEVICE")
    ):
        """MIG SHIELD: Trigger a drone emergency response mission."""
        try:
            # Enrich actor with missing context if needed for the engine
            full_actor = actor.copy()
            if "identity_id" not in full_actor: full_actor["identity_id"] = x_aegis_identity
            if "device_id" not in full_actor: full_actor["device_id"] = x_aegis_device

            return await mig_shield_engine.dispatch_mission(full_actor, data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/kpis")
    async def get_kpis(actor: dict = Depends(get_actor_ctx)):
        """MIG SHIELD: Retrieve 3-30-3 KPI validation report."""
        return mig_shield_engine.get_kpis()

    return router
