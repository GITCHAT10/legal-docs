from fastapi import APIRouter, Depends, Header, HTTPException

def create_commerce_router(imoxon, catalog, merchant, pos, procurement, get_actor_ctx):
    router = APIRouter(prefix="/commerce", tags=["commerce"])

    @router.post("/vendors/approve")
    async def approve_vendor(data: dict, actor: dict = Depends(get_actor_ctx)):
        return merchant.approve_vendor(actor, data)

    @router.post("/coupon/campaign")
    async def create_campaign(data: dict, actor: dict = Depends(get_actor_ctx)):
        return imoxon.campaign_manager.create_campaign(actor, data)

    @router.post("/orders/create")
    async def create_order(data: dict, actor: dict = Depends(get_actor_ctx)):
        return procurement.create_order(actor, data)

    @router.post("/milestones/verify")
    async def verify_milestone(data: dict, actor: dict = Depends(get_actor_ctx)):
        return imoxon.execute_commerce_action("imoxon.milestone.verify", actor, lambda: {"status": "VERIFIED", "data": data})

    @router.post("/pos/stock")
    async def sync_stock(data: dict, actor: dict = Depends(get_actor_ctx)):
        return pos.sync_stock(actor, data)

    return router
