from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List

def create_upos_router(upos_engine, edge_node, get_actor_ctx):
    router = APIRouter()

    @router.post("/upos/order")
    async def create_order(data: Dict, actor: Dict = Depends(get_actor_ctx)):
        if not edge_node.online:
            res = edge_node.record_transaction({
                "event_type": "upos.order.completed",
                "actor_id": actor["identity_id"],
                "payload": data
            })
            return {"status": "OFFLINE_QUEUED", "detail": res}

        return upos_engine.create_order(
            merchant_id=data.get("merchant_id"),
            actor_id=actor["identity_id"],
            items=data.get("items"),
            amount=data.get("amount")
        )

    return router
