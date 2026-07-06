from fastapi import APIRouter, Depends, HTTPException

def create_itravel_router(mars_engine, get_actor_ctx):
    router = APIRouter(prefix="/itravel", tags=["itravel"])

    @router.post("/packages/build")
    async def build_package(config: dict, actor: dict = Depends(get_actor_ctx)):
        """TRAWEL: Build a demand-predicted package."""
        return mars_engine.predict_and_build_package(actor, config)

    @router.post("/orders/full-cycle")
    async def create_full_cycle_order(guest_id: str, package_id: str, actor: dict = Depends(get_actor_ctx)):
        """NEXUS SKY-i: Trigger full closed-loop economy cycle."""
        try:
            return mars_engine.process_full_cycle(actor, guest_id, package_id)
        except Exception as e:
            # Unwrap ValueError if wrapped by ExecutionGuard or other layers
            err_msg = str(e)
            if "Invalid Package" in err_msg:
                 raise HTTPException(status_code=400, detail="Invalid Package")
            raise e

    @router.post("/orders/finalize")
    async def finalize_order(order_id: str, actor: dict = Depends(get_actor_ctx)):
        """NEXUS SKY-i: Finalize order and release payouts."""
        result = mars_engine.finalize_cycle(actor, order_id)
        if not result:
            raise HTTPException(status_code=404, detail="Order not found")
        return result

    @router.post("/orders/create")
    async def create_order(vendor_id: str, amount: float, passenger_type: str = "adult", actor: dict = Depends(get_actor_ctx)):
        """LEGACY: Create an order via compatibility adapter."""
        return mars_engine.create_order(actor, {"vendor_id": vendor_id, "amount": amount, "passenger_type": passenger_type})

    return router

def create_flow_router(mars_engine, get_actor_ctx):
    router = APIRouter(prefix="/flow", tags=["flow"])

    @router.post("/transfer/dispatch")
    async def dispatch_transfer(order_id: str, transfer_data: dict, actor: dict = Depends(get_actor_ctx)):
        """UT SYSTEM: Dispatch a physical transfer."""
        return mars_engine.execute_transfer(actor, order_id, transfer_data)

    @router.post("/delivery/update")
    async def update_delivery(order_id: str, status: str, actor: dict = Depends(get_actor_ctx)):
        """LEGACY: Update delivery status and trigger finalize."""
        # For compatibility with test_maafushi_guest_order_flow
        if status == "DELIVERED":
             res = mars_engine.finalize_cycle(actor, order_id)
             if res:
                 return {"delivery_status": "DELIVERED", "order": res}
        raise HTTPException(status_code=400, detail="Invalid status")

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
