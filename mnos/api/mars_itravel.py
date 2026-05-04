from fastapi import APIRouter, Depends, HTTPException
from mnos.shared.execution_guard import _sovereign_context
import uuid
from decimal import Decimal

def create_itravel_router(mars_engine, get_actor_ctx):
    router = APIRouter(prefix="/itravel", tags=["itravel"])

    @router.post("/packages/build")
    async def build_package(config: dict, actor: dict = Depends(get_actor_ctx)):
        """TRAWEL: Build a demand-predicted package."""
        _sovereign_context.set({"token": str(uuid.uuid4()), "actor": actor})
        try:
            return mars_engine.predict_and_build_package(actor, config)
        finally:
            _sovereign_context.set(None)

    @router.post("/orders/full-cycle")
    async def create_full_cycle_order(guest_id: str, package_id: str, actor: dict = Depends(get_actor_ctx)):
        """NEXUS SKY-i: Trigger full closed-loop economy cycle."""
        _sovereign_context.set({"token": str(uuid.uuid4()), "actor": actor})
        try:
            return mars_engine.process_full_cycle(actor, guest_id, package_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            _sovereign_context.set(None)

    @router.post("/orders/finalize")
    async def finalize_order(order_id: str, actor: dict = Depends(get_actor_ctx)):
        """NEXUS SKY-i: Finalize order and release payouts."""
        _sovereign_context.set({"token": str(uuid.uuid4()), "actor": actor})
        try:
            result = mars_engine.finalize_cycle(actor, order_id)
            if not result:
                raise HTTPException(status_code=400, detail="Order not found or finalize failed")
            return result
        finally:
            _sovereign_context.set(None)

    return router

def create_flow_router(mars_engine, get_actor_ctx):
    router = APIRouter(prefix="/flow", tags=["flow"])

    @router.post("/transfer/dispatch")
    async def dispatch_transfer(order_id: str, transfer_data: dict, actor: dict = Depends(get_actor_ctx)):
        """UT SYSTEM: Dispatch a physical transfer."""
        _sovereign_context.set({"token": str(uuid.uuid4()), "actor": actor})
        try:
            return mars_engine.execute_transfer(actor, order_id, transfer_data)
        finally:
            _sovereign_context.set(None)

    return router

def create_grid_router(mars_engine, get_actor_ctx):
    router = APIRouter(prefix="/grid-control", tags=["grid-control"])

    @router.get("/dashboard")
    async def get_dashboard(actor: dict = Depends(get_actor_ctx)):
        """MARS-GRID-CONTROL Dashboard."""
        if actor.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        # Simplified stats for demo
        return {
            "total_orders": len(mars_engine.orders),
            "revenue": sum(o["pricing"]["total"] for o in mars_engine.orders.values())
        }

    return router
