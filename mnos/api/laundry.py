from fastapi import APIRouter, Depends, HTTPException
from mnos.shared.execution_guard import _sovereign_context
import uuid
from typing import List

def create_laundry_router(laundry_engine, get_actor_ctx):
    router = APIRouter(prefix="/laundry", tags=["laundry-service"])

    @router.post("/store/register")
    async def register_store(data: dict, actor: dict = Depends(get_actor_ctx)):
        """MIG/GM: Register multi-store laundry facility."""
        _sovereign_context.set({"token": str(uuid.uuid4()), "actor": actor})
        try:
            return laundry_engine.register_laundry_store(actor, data)
        finally:
            _sovereign_context.set(None)

    @router.post("/order")
    async def create_order(store_id: str, items: List[dict], actor: dict = Depends(get_actor_ctx)):
        """Guest: Book laundry service."""
        _sovereign_context.set({"token": str(uuid.uuid4()), "actor": actor})
        try:
            return laundry_engine.create_laundry_order(actor, store_id, items)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            _sovereign_context.set(None)

    @router.post("/order/update")
    async def update_status(order_id: str, status: str, actor: dict = Depends(get_actor_ctx)):
        """Execution: Update order lifecycle."""
        _sovereign_context.set({"token": str(uuid.uuid4()), "actor": actor})
        try:
            result = laundry_engine.update_order_status(actor, order_id, status)
            if not result:
                raise HTTPException(status_code=404, detail="Order not found")
            return result
        finally:
            _sovereign_context.set(None)

    @router.get("/stores")
    async def get_stores():
        """Public/Guest: List available laundry facilities."""
        return list(laundry_engine.stores.values())

    return router
