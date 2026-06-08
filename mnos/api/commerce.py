from fastapi import APIRouter, Depends

def create_commerce_router(imoxon, catalog, merchant, pos, procurement, get_actor_ctx):
    router = APIRouter(tags=["commerce"])

    @router.post("/vendors/approve")
    async def approve_vendor(data: dict, actor: dict = Depends(get_actor_ctx)):
        return merchant.approve_vendor(actor, data)

    @router.post("/coupon/campaign")
    async def create_campaign(data: dict, actor: dict = Depends(get_actor_ctx)):
        return imoxon.campaign_manager.create_campaign(actor, data)

    @router.post("/orders/create")
    async def create_order(data: dict, actor: dict = Depends(get_actor_ctx)):
        return procurement.create_purchase_request(actor, data.get("items"), data.get("amount"))

    @router.post("/orders/approve")
    async def approve_order(order_id: str, actor: dict = Depends(get_actor_ctx)):
        return procurement.approve_order(actor, order_id)

    @router.post("/orders/dispatch")
    async def dispatch_order(order_id: str, actor: dict = Depends(get_actor_ctx)):
        return procurement.mark_dispatched(actor, order_id)

    @router.post("/orders/deliver")
    async def deliver_order(order_id: str, actor: dict = Depends(get_actor_ctx)):
        return procurement.mark_delivered(actor, order_id)

    @router.post("/orders/invoice")
    async def invoice_order(order_id: str, actor: dict = Depends(get_actor_ctx)):
        return procurement.finalize_invoice(actor, order_id)

    @router.post("/orders/settle")
    async def settle_order(order_id: str, actor: dict = Depends(get_actor_ctx)):
        return procurement.settle_payment(actor, order_id)

    @router.post("/milestones/verify")
    async def verify_milestone(data: dict, actor: dict = Depends(get_actor_ctx)):
        return imoxon.execute_commerce_action("imoxon.milestone.verify", actor, lambda: {"status": "VERIFIED", "data": data})

    @router.post("/pos/stock")
    async def sync_stock(data: dict, actor: dict = Depends(get_actor_ctx)):
        return pos.sync_stock(actor, data)

    return router
