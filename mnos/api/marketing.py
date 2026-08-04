from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException


def create_marketing_router(engine, get_actor_ctx):
    router = APIRouter(prefix="/marketing", tags=["sovereign-marketing"])

    def handle(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/brands")
    async def register_brand(data: dict, actor: dict = Depends(get_actor_ctx)):
        return handle(engine.register_brand, actor, data)

    @router.get("/brands")
    async def list_brands(actor: dict = Depends(get_actor_ctx)):
        engine._require(actor, engine.OPERATOR_ROLES)
        return list(engine.brands.values())

    @router.post("/campaigns")
    async def create_campaign(data: dict, actor: dict = Depends(get_actor_ctx)):
        return handle(engine.create_campaign, actor, data)

    @router.get("/campaigns")
    async def list_campaigns(brand_id: Optional[str] = None, actor: dict = Depends(get_actor_ctx)):
        engine._require(actor, engine.OPERATOR_ROLES)
        return [c for c in engine.campaigns.values() if not brand_id or c["brand_id"] == brand_id]

    @router.post("/campaigns/{campaign_id}/submit")
    async def submit_campaign(campaign_id: str, actor: dict = Depends(get_actor_ctx)):
        return handle(engine.submit_campaign, actor, campaign_id)

    @router.post("/campaigns/{campaign_id}/approval")
    async def approve_campaign(campaign_id: str, data: dict, actor: dict = Depends(get_actor_ctx)):
        return handle(
            engine.approve_campaign,
            actor,
            campaign_id,
            str(data.get("decision", "")),
            data.get("reason"),
        )

    @router.post("/campaigns/{campaign_id}/activate")
    async def activate_campaign(campaign_id: str, actor: dict = Depends(get_actor_ctx)):
        return handle(engine.activate_campaign, actor, campaign_id)

    @router.post("/campaigns/{campaign_id}/spend")
    async def record_spend(campaign_id: str, data: dict, actor: dict = Depends(get_actor_ctx)):
        return handle(
            engine.record_spend,
            actor,
            campaign_id,
            Decimal(str(data.get("amount", "0"))),
            str(data.get("external_ref") or "MANUAL"),
        )

    @router.post("/content")
    async def create_content(data: dict, actor: dict = Depends(get_actor_ctx)):
        return handle(engine.create_content, actor, data)

    @router.post("/leads")
    async def capture_lead(data: dict, actor: dict = Depends(get_actor_ctx)):
        return handle(engine.capture_lead, actor, data)

    @router.post("/conversions")
    async def record_conversion(data: dict, actor: dict = Depends(get_actor_ctx)):
        return handle(engine.record_conversion, actor, data)

    @router.get("/dashboard")
    async def dashboard(brand_id: Optional[str] = None, actor: dict = Depends(get_actor_ctx)):
        return handle(engine.dashboard, actor, brand_id)

    return router
