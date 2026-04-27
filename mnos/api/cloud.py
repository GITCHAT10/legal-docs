from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

def create_cloud_router(tenant_manager, compute_manager, orca_center, failover_orch, get_actor_ctx):
    router = APIRouter(prefix="/cloud", tags=["cloud"])

    @router.get("/failover/status")
    async def get_failover_status(actor: dict = Depends(get_actor_ctx)):
        status = failover_orch.get_failover_status()
        # Enforce ORCA failover status requirements
        status["heartbeat_health"] = failover_orch.heartbeat.node_status
        return status

    @router.post("/failover/promote")
    async def promote_node(node_id: str, remote_hash: str, actor: dict = Depends(get_actor_ctx)):
        if actor.get("role") != "admin":
             raise HTTPException(status_code=403, detail="Only admins can trigger manual promotion")
        try:
            return failover_orch.trigger_failover(node_id, remote_hash)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

    @router.post("/tenants/provision")
    async def provision_tenant(name: str, tenant_type: str, island_id: str, actor: dict = Depends(get_actor_ctx)):
        if actor.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only admins can provision tenants")
        return tenant_manager.provision_tenant(actor, name, tenant_type, island_id)

    @router.get("/health")
    async def get_cloud_health(actor: dict = Depends(get_actor_ctx)):
        return orca_center.get_national_health_report()

    @router.post("/compute/allocate")
    async def allocate_resource(sensitivity: str, actor: dict = Depends(get_actor_ctx)):
        return compute_manager.allocate_ai_resource(sensitivity)

    return router
