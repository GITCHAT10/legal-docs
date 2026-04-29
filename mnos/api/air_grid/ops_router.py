from fastapi import APIRouter, Depends, HTTPException
from mnos.modules.air_grid.ut_bridge import UTMVPBridge

def create_ops_router(bridge: UTMVPBridge, get_actor_ctx):
    router = APIRouter(prefix="/ops", tags=["ops-desk"])

    @router.get("/adjustments/pending")
    async def get_pending_adjustments(actor: dict = Depends(get_actor_ctx)):
        # RBAC: Only ops_lead or admin
        if actor.get("role") not in ["ops_lead", "admin"]:
            raise HTTPException(status_code=403, detail="FORBIDDEN: Ops Lead access required")
        return list(bridge.pending_adjustments.values())

    @router.post("/adjustments/{adj_id}/process")
    async def process_adjustment(adj_id: str, action: str, actor: dict = Depends(get_actor_ctx)):
        if actor.get("role") not in ["ops_lead", "admin"]:
            raise HTTPException(status_code=403, detail="FORBIDDEN: Ops Lead access required")
        return bridge.process_manual_override(actor, adj_id, action)

    return router
