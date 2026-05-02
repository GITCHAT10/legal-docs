from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List
from mnos.modules.imoxon.supplier.rate_models import ChannelType, MarketSellingRate

def create_supplier_rate_router(engine, get_actor_ctx):
    router = APIRouter(tags=["supplier-portal"])

    @router.post("/rates/intake")
    async def intake_rate(payload: dict = Body(...), actor: dict = Depends(get_actor_ctx)):
        """PH Supplier Portal: Intake new contract rate."""
        return engine.intake_contract_rate(actor, payload)

    @router.post("/rates/{rate_id}/approve")
    async def approve_rate(rate_id: str, stage: str, actor: dict = Depends(get_actor_ctx)):
        """PH Supplier Portal: Multi-stage rate approval."""
        return engine.approve_rate(actor, rate_id, stage)

    @router.get("/rates/{rate_id}")
    async def get_rate(rate_id: str, channel: ChannelType, actor: dict = Depends(get_actor_ctx)):
        """Market Selling Rate: Retrieve channel-specific rate."""
        try:
            return engine.get_market_selling_rate(channel, rate_id, actor)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router
