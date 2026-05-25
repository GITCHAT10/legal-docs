from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List
from mnos.modules.prestige.supplier_portal.models import ChannelType

def create_prestige_supplier_router(portal, get_actor_ctx):
    router = APIRouter(tags=["prestige-supplier-portal"])

    @router.post("/contracts/upload")
    async def upload_contract(supplier_id: str, resort_name: str, file_name: str, actor: dict = Depends(get_actor_ctx)):
        return portal.upload_contract_pdf(actor, supplier_id, resort_name, file_name)

    @router.post("/rate-sheets/upload")
    async def upload_rate_sheet(payload: dict = Body(...), actor: dict = Depends(get_actor_ctx)):
        return portal.submit_rate_sheet(actor, payload)

    @router.post("/extraction/confirm")
    async def confirm_extraction(rate_id: str, actor: dict = Depends(get_actor_ctx)):
        return {"rate_id": rate_id, "status": "CONFIRMED"}

    @router.post("/finance/review")
    async def finance_review(rate_id: str, decision: str = "APPROVE", actor: dict = Depends(get_actor_ctx)):
        return portal.approve_stage(actor, rate_id, "FINANCE", decision)

    @router.post("/revenue/review")
    async def revenue_review(rate_id: str, decision: str = "APPROVE", actor: dict = Depends(get_actor_ctx)):
        return portal.approve_stage(actor, rate_id, "REVENUE", decision)

    @router.post("/cmo/market-strategy")
    async def cmo_market_strategy(rate_id: str, decision: str = "APPROVE", actor: dict = Depends(get_actor_ctx)):
        return portal.approve_stage(actor, rate_id, "CMO", decision)

    @router.post("/market-rates/generate")
    async def generate_market_rates(payload: dict = Body(...), actor: dict = Depends(get_actor_ctx)):
        return portal.submit_rate_sheet(actor, payload)

    @router.post("/specials/submit")
    async def submit_special(payload: dict = Body(...), actor: dict = Depends(get_actor_ctx)):
        return portal.submit_special(actor, payload)

    @router.post("/stop-sell")
    async def stop_sell(product_id: str, actor: dict = Depends(get_actor_ctx)):
        return portal.stop_sell(actor, product_id)

    @router.post("/open-sale")
    async def open_sale(product_id: str, actor: dict = Depends(get_actor_ctx)):
        return portal.request_open_sale(product_id)

    @router.post("/allotment/update")
    async def update_allotment(product_id: str, count: int, actor: dict = Depends(get_actor_ctx)):
        return portal.update_allotment(product_id, count)

    @router.post("/admin/approve")
    async def admin_approve(rate_id: str, actor: dict = Depends(get_actor_ctx)):
        return portal.approve_stage(actor, rate_id, "CMO", "APPROVE")

    @router.post("/channel/distribute")
    async def channel_distribute(rate_id: str, actor: dict = Depends(get_actor_ctx)):
        return {"rate_id": rate_id, "status": "DISTRIBUTED", "channels": ["SiteMinder", "Booking.com"]}

    @router.get("/rates/{rate_id}")
    async def get_published_rate(rate_id: str, channel: ChannelType, actor: dict = Depends(get_actor_ctx)):
        try:
            return portal.get_rate(actor, rate_id, channel)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router
