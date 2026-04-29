from fastapi import APIRouter, Header, Depends, HTTPException, Request
from typing import Dict, Any
import uuid

def create_fce_gateway_router(gateway_engine, get_actor_ctx):
    router = APIRouter()

    @router.post("/{provider}/webhook")
    async def provider_webhook(provider: str, request: Request, x_gateway_signature: str = Header(...)):
        payload = await request.json()
        trace_id = f"TR-GW-{uuid.uuid4().hex[:6]}"
        try:
            return gateway_engine.process_webhook(provider, payload, x_gateway_signature, trace_id)
        except PermissionError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/payments/status/{invoice_id}")
    async def get_payment_status(invoice_id: str):
        return gateway_engine.reconcile_by_reference(invoice_id)

    return router
