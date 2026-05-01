from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List
from mnos.modules.prestige.supplier_portal.models import SupplierAction, AdminApprovalTask

def create_supplier_portal_router(orchestrator, finance, revenue, cmo, rate_engine, specials, stop_sell, open_sale, get_actor_ctx):
    router = APIRouter(prefix="/supplier-portal", tags=["supplier-portal"])

    @router.post("/contracts/upload")
    async def upload_contract(filename: str, actor: dict = Depends(get_actor_ctx)):
        # Doctrine: Supplier confirms data, upload creates draft
        return {"status": "success", "action_id": "ACT-CONTRACT-UPLOAD", "extracted_status": "DRAFT"}

    @router.post("/rate-sheets/upload")
    async def upload_rate_sheet(csv_content: str = Body(...), actor: dict = Depends(get_actor_ctx)):
        return {"status": "success", "action_id": "ACT-RATE-UPLOAD", "extracted_status": "DRAFT"}

    @router.post("/finance/review")
    async def finance_review(task_id: str, decision: str, comments: str = None, actor: dict = Depends(get_actor_ctx)):
        return orchestrator.record_decision(task_id, "FINANCE", actor["identity_id"], decision, {"comments": comments})

    @router.post("/revenue/review")
    async def revenue_review(task_id: str, decision: str, comments: str = None, actor: dict = Depends(get_actor_ctx)):
        return orchestrator.record_decision(task_id, "REVENUE", actor["identity_id"], decision, {"comments": comments})

    @router.post("/market-rates/generate")
    async def generate_rates(net_rate: float, category: str, resort_id: str, actor: dict = Depends(get_actor_ctx)):
        strategy = cmo.get_strategy(resort_id)
        return rate_engine.generate_market_rates(net_rate, category, strategy)

    @router.post("/stop-sell")
    async def stop_sell_action(payload: Dict[str, Any], actor: dict = Depends(get_actor_ctx)):
        return stop_sell.submit_stop_sell(actor, payload)

    @router.post("/open-sale")
    async def open_sale_action(payload: Dict[str, Any], actor: dict = Depends(get_actor_ctx)):
        return open_sale.request_open_sale(actor, payload)

    return router
