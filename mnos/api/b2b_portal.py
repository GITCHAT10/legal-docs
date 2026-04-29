from fastapi import APIRouter, Depends, HTTPException
from typing import List

def create_b2b_portal_router(nexus_brain, b2b_negotiator, get_actor_ctx):
    router = APIRouter(prefix="/b2b", tags=["b2b-portal"])

    @router.post("/rfq")
    async def request_quote(rfq_data: dict, actor: dict = Depends(get_actor_ctx)):
        """Auto-Negotiation: Request for Quote (TO vs DMC)."""
        from mnos.shared.execution_guard import ExecutionGuard
        try:
            with ExecutionGuard.authorized_context(actor):
                return b2b_negotiator.process_rfq(actor, rfq_data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/booking/confirm")
    async def confirm_booking(quote_id: str, actor: dict = Depends(get_actor_ctx)):
        """Instant Booking: Confirm quote and lock inventory."""
        from mnos.shared.execution_guard import ExecutionGuard
        try:
            with ExecutionGuard.authorized_context(actor):
                return b2b_negotiator.confirm_booking(actor, quote_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/inventory/search")
    async def search_inventory(actor: dict = Depends(get_actor_ctx)):
        """B2B: Search available inventory packages."""
        if actor.get("realm") not in ["B2B", "API_DIRECT"]:
             raise HTTPException(status_code=403, detail="B2B Realm access required")
        return nexus_brain.get_inventory_search(actor, {})

    @router.get("/commissions")
    async def get_commissions(actor: dict = Depends(get_actor_ctx)):
        """B2B: Agent commission report."""
        return {"agent_id": actor["identity_id"], "total_earned": 1250.0, "currency": "USD"}

    return router
