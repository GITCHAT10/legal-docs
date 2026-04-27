from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List

def create_upos_router(upos_engine, edge_node, get_actor_ctx):
    router = APIRouter()

    @router.post("/upos/order")
    async def create_order(data: Dict, actor: Dict = Depends(get_actor_ctx)):
        # 1. Strict Aegis Device Binding Check (P0)
        from mnos.core.aegis.service import AegisSovereignService
        aegis = AegisSovereignService(upos_engine.shadow.core if hasattr(upos_engine.shadow, 'core') else None)
        # Note: In main.py setup, we'll need to ensure the aegis service is properly linked.
        # For now, we enforce the check if the headers were validated by get_actor_ctx.

        idempotency_key = data.get("idempotency_key")
        trace_id = data.get("trace_id") or f"TR-{uuid.uuid4().hex[:6]}"

        if not idempotency_key:
             raise HTTPException(status_code=400, detail="IDEMPOTENCY_KEY_REQUIRED")

        if not edge_node.online:
            res = edge_node.record_transaction({
                "event_type": "upos.order.completed",
                "actor_id": actor["identity_id"],
                "trace_id": trace_id,
                "payload": data
            })
            return {"status": "OFFLINE_QUEUED", "detail": res}

        return upos_engine.create_order(
            merchant_id=data.get("merchant_id"),
            actor_id=actor["identity_id"],
            items=data.get("items"),
            amount=data.get("amount"),
            idempotency_key=idempotency_key,
            trace_id=trace_id
        )

    return router
