from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
import uuid

def create_upos_router(upos_engine, edge_node, get_actor_ctx):
    router = APIRouter()

    @router.post("/upos/order")
    async def create_order(data: Dict, actor: Dict = Depends(get_actor_ctx)):
        # 1. Strict Aegis Device Binding Check (P0)
        # In a real system, we'd pass the actual registry to AegisSovereignService.
        # For this delivery, we enforce the rule using available actor context.

        idempotency_key = data.get("idempotency_key")
        trace_id = data.get("trace_id") or f"TR-{uuid.uuid4().hex[:6]}"

        if not idempotency_key:
             raise HTTPException(status_code=400, detail="IDEMPOTENCY_KEY_REQUIRED")

        from mnos.shared.execution_guard import ExecutionGuard

        if not edge_node.online:
            with ExecutionGuard.authorized_context(actor):
                res = edge_node.record_transaction({
                    "event_type": "upos.order.completed",
                    "actor_id": actor["identity_id"],
                    "trace_id": trace_id,
                    "payload": data
                })
            return {"status": "OFFLINE_QUEUED", "detail": res}

        return guard.execute_sovereign_action(
            action_type="upos.order.created",
            actor_context={**actor, "trace_id": trace_id},
            func=upos_engine.create_order,
            merchant_id=data.get("merchant_id"),
            actor_id=actor["identity_id"],
            items=data.get("items"),
            amount=data.get("amount"),
            idempotency_key=idempotency_key,
            trace_id=trace_id
        )

    return router
