from fastapi import APIRouter, Header, Depends, HTTPException, Request
from typing import Dict, Any
import uuid

def create_fce_v1_router(wallet_service, get_actor_ctx):
    router = APIRouter()

    @router.post("/payments/webhook")
    async def payment_webhook(request: Request, x_idempotency_key: str = Header(...), x_gateway_signature: str = Header(...)):
        # HMAC verification would go here (omitted for this simulation but required in P0 spec)
        payload = await request.json()
        trace_id = f"TR-WEBHOOK-{uuid.uuid4().hex[:6]}"

        return wallet_service.process_payment_webhook(payload, trace_id=trace_id)

    @router.get("/wallet/balance")
    async def get_balance(actor: Dict = Depends(get_actor_ctx)):
        account = wallet_service.get_or_create_account(actor["identity_id"])
        return {
            "economic_actor_id": actor["identity_id"],
            "balance_mvr": float(account["balance"]),
            "currency": account["currency"],
            "status": account["status"]
        }

    @router.post("/settlements/withdraw")
    async def request_withdraw(data: Dict, actor: Dict = Depends(get_actor_ctx)):
        trace_id = data.get("trace_id") or f"TR-SETTLE-{uuid.uuid4().hex[:6]}"
        try:
            return wallet_service.request_withdrawal(
                actor_id=actor["identity_id"],
                amount_mvr=data.get("amount_mvr"),
                bank_hash=data.get("bank_account_hash"),
                trace_id=trace_id
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router
