from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

def create_cloud_router(tenant_manager, compute_manager, orca_center, get_actor_ctx):
    router = APIRouter(prefix="/cloud", tags=["cloud"])

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
