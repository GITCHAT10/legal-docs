from fastapi import APIRouter, Depends, Request

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

    @router.post("/products/import")
    async def import_product(request: Request, sid: str, actor: dict = Depends(get_actor_ctx)):
        # raw is list of products or a single product
        raw = await request.json()
        items = raw if isinstance(raw, list) else [raw]
        import_results = []
        for item in items:
            res = catalog.import_supplier_product(actor, sid, item)
            res["id"] = res.get("id")
            import_results.append(res)
        return {"products": import_results}

    @router.post("/products/approve")
    async def approve_product(pid: str, actor: dict = Depends(get_actor_ctx)):
        return catalog.approve_product(actor, pid)

    @router.get("/catalog")
    async def get_catalog():
        return catalog.products

    @router.post("/milestones/verify")
    async def verify_milestone(data: dict, actor: dict = Depends(get_actor_ctx)):
        return imoxon.execute_commerce_action("imoxon.milestone.verify", actor, lambda: {"status": "VERIFIED", "data": data})

    @router.post("/pricing/landed-cost")
    async def get_landed_cost(base: float, cat: str = "RESORT_SUPPLY", actor: dict = Depends(get_actor_ctx)):
        # 1. Logistics + Markup (15% + 10% = 1.265)
        landed_base = base * 1.15 * 1.10
        # 2. FCE Finalization (SC + TGST)
        pricing = imoxon.fce.finalize_invoice(landed_base, cat)
        return pricing

    @router.post("/pos/stock")
    async def sync_stock(data: dict, actor: dict = Depends(get_actor_ctx)):
        return pos.sync_stock(actor, data)

    return router
