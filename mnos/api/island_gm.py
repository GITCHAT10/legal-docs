from fastapi import APIRouter, Depends, HTTPException

def create_island_gm_router(island_gm_system, vvip_engine, get_actor_ctx):
    router = APIRouter(prefix="/island-gm", tags=["island-gm"])

    @router.post("/registry/setup")
    async def setup_island(data: dict, actor: dict = Depends(get_actor_ctx)):
        """MIG Central: Register a new island node."""
        if actor.get("role") != "admin":
             raise HTTPException(status_code=403, detail="Admin access required")
        return island_gm_system.register_island(actor, data)

    @router.post("/vendors/onboard")
    async def onboard_vendor(data: dict, actor: dict = Depends(get_actor_ctx)):
        """Island GM: Onboard local vendor."""
        try:
            return island_gm_system.onboard_vendor_local(actor, data)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

    @router.get("/dashboard")
    async def get_dashboard(island: str, actor: dict = Depends(get_actor_ctx)):
        """Island GM: Fetch island command panel."""
        try:
            result = island_gm_system.get_gm_dashboard(actor, island)
            if not result:
                raise HTTPException(status_code=404, detail="Island stats not found")
            return result
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

    @router.post("/vvip/key/mint")
    async def mint_vvip_key(recipient_id: str, asset_id: str, actor: dict = Depends(get_actor_ctx)):
        """MIG Action: Mint VVIP Reward Key."""
        try:
            return vvip_engine.mint_vvip_key(actor, recipient_id, asset_id)
        except (PermissionError, ValueError) as e:
            raise HTTPException(status_code=403 if isinstance(e, PermissionError) else 400, detail=str(e))

    @router.post("/vvip/key/verify")
    async def verify_vvip_key(key_id: str, actor: dict = Depends(get_actor_ctx)):
        """Asset Controller Action: Verify QR/NFC access."""
        success = vvip_engine.verify_access(actor, key_id)
        if not success:
             raise HTTPException(status_code=403, detail="VVIP Access Denied")
        return {"status": "ACCESS_GRANTED"}

    return router
