from fastapi import APIRouter, Depends, Body
from typing import List

def create_restaurant_router(restaurant_engine, get_actor_ctx):
    router = APIRouter(prefix="/restaurant", tags=["restaurant"])

    @router.post("/register")
    async def register_restaurant(data: dict, actor: dict = Depends(get_actor_ctx)):
        return restaurant_engine.register_restaurant(actor, data)

    @router.post("/voice-order")
    async def voice_order(rest_id: str, transcript: str, actor: dict = Depends(get_actor_ctx)):
        return restaurant_engine.process_voice_order(actor, rest_id, transcript)

    @router.post("/order")
    async def create_order(rest_id: str, data: dict, actor: dict = Depends(get_actor_ctx)):
        return restaurant_engine.create_order(actor, rest_id, data)

    @router.get("/analytics/forecast")
    async def get_forecast(rest_id: str, actor: dict = Depends(get_actor_ctx)):
        return restaurant_engine.get_ai_demand_forecast(rest_id)

    @router.post("/pos/sync-offline")
    async def sync_offline(merchant_id: str, transactions: List[dict] = Body(...), actor: dict = Depends(get_actor_ctx)):
        return restaurant_engine.core.execute_commerce_action(
            "bpe.offline_sync",
            actor,
            restaurant_engine.bpe.sync_offline_batch,
            merchant_id, transactions
        )

    return router
