from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

class OrderRequest(BaseModel):
    amount: float
    vendor_id: str
    items: List[dict] = []

class PaymentExecutionRequest(BaseModel):
    intent_id: str
    payment_method: str = "QR_PAY"

def create_upos_router(engine, ledger, get_actor_ctx):
    router = APIRouter(tags=["upos"])

    @router.post("/upos/order/create")
    async def create_order(req: OrderRequest, actor: dict = Depends(get_actor_ctx)):
        """UPOS: Create order and finalize pricing."""
        return engine.create_payment_intent(actor, req.model_dump())

    @router.post("/upos/payment/execute")
    async def execute_payment(req: PaymentExecutionRequest, actor: dict = Depends(get_actor_ctx)):
        """UPOS: Execute payment and split funds."""
        return engine.execute_payment(actor, req.intent_id, req.payment_method)

    @router.get("/upos/wallet/balance")
    async def get_balance(currency: str = "MVR", actor: dict = Depends(get_actor_ctx)):
        """UPOS: Get real-time wallet balance."""
        balance = ledger.get_balance(actor["identity_id"], currency)
        return {"balance": float(balance), "currency": currency}

    return router
