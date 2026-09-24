from fastapi import APIRouter, Depends, HTTPException


def create_brain_coral_router(brain_coral_bridge, get_actor_ctx):
    router = APIRouter(prefix="/brain-coral", tags=["brain-coral"])

    @router.get("/status")
    async def get_operational_status(actor: dict = Depends(get_actor_ctx)):
        """BRAIN CORAL read-only operational intelligence endpoint."""
        try:
            return brain_coral_bridge.read_operational_status(actor)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))

    @router.post("/action-request")
    async def request_governed_action(data: dict, actor: dict = Depends(get_actor_ctx)):
        """Queue a governed action request without executing restricted mutations."""
        try:
            return brain_coral_bridge.request_governed_action(actor, data)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    return router
