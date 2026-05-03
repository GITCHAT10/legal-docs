from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ..quote_bridge.quote_models import QuoteRequest, QuoteResponse, QuoteStatus
from ..quote_bridge.fce_quote_bridge import FCEQuoteBridge
from ..audit.shadow_quote_events import create_shadow_event

router = APIRouter(prefix="/fce/quotes", tags=["FCE Quotes"])
bridge = FCEQuoteBridge()

@router.post("/request")
async def request_quote(request: QuoteRequest):
    try:
        response = bridge.process_quote_request(request, {"actor_type": "system", "actor_id": "API"})
        return {
            "request_id": response.request_id,
            "lead_id": response.lead_id,
            "status": "pending", # Prompt says return pending initially
            "shadow_event": "FCE_QUOTE_REQUESTED",
            "audit_hash": response.shadow.audit_hash
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: str):
    if quote_id not in bridge.quotes:
        raise HTTPException(status_code=404, detail="Quote not found")
    return bridge.quotes[quote_id]

@router.get("/request/{request_id}")
async def get_request_status(request_id: str):
    # Search for quote with this request_id
    for quote in bridge.quotes.values():
        if quote.request_id == request_id:
            return {
                "request_id": request_id,
                "status": quote.status,
                "quote_id": quote.quote_id
            }
    return {
        "request_id": request_id,
        "status": "pending",
        "quote_id": None
    }

@router.post("/{quote_id}/verify")
async def verify_quote(quote_id: str, actor_ctx: Dict = {"actor_id": "SYSTEM"}):
    if quote_id not in bridge.quotes:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote = bridge.quotes[quote_id]
    quote.status = QuoteStatus.VERIFIED
    quote.approval.fce_verified = True
    quote.approval.human_can_send = True

    event = create_shadow_event(
        event_type="FCE_QUOTE_VERIFIED",
        lead_id=quote.lead_id,
        actor_type="system",
        actor_id=actor_ctx["actor_id"],
        parent_hash=quote.shadow.audit_hash,
        correlation_id=quote.shadow.parent_hash,
        payload={"quote_id": quote_id},
        quote_id=quote_id
    )
    # Update quote shadow metadata with new hash
    quote.shadow.audit_hash = event["hash"]
    quote.shadow.event = "FCE_QUOTE_VERIFIED"

    return {"status": "verified", "audit_hash": event["hash"]}

@router.post("/{quote_id}/revise")
async def revise_quote(quote_id: str, actor_ctx: Dict):
    if quote_id not in bridge.quotes:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote = bridge.quotes[quote_id]
    quote.status = QuoteStatus.REVISION_REQUESTED

    event = create_shadow_event(
        event_type="QUOTE_REVISION_REQUESTED",
        lead_id=quote.lead_id,
        actor_type="human",
        actor_id=actor_ctx["actor_id"],
        parent_hash=quote.shadow.audit_hash,
        correlation_id=quote.shadow.parent_hash,
        payload={"reason": "Manual revision requested"},
        quote_id=quote_id
    )
    # Update quote shadow metadata
    quote.shadow.audit_hash = event["hash"]
    quote.shadow.event = "QUOTE_REVISION_REQUESTED"

    return {"status": "revision_requested", "audit_hash": event["hash"]}
