from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..quote_bridge.quote_models import QuoteStatus
from ..audit.shadow_quote_events import create_shadow_event
from .quote_routes import bridge

router = APIRouter(prefix="/social/leads", tags=["Social Leads"])

# Mock database for lead SHADOW chains
lead_chains = {}

@router.post("/{lead_id}/attach-quote")
async def attach_quote(lead_id: str, quote_id: str):
    if quote_id not in bridge.quotes:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote = bridge.quotes[quote_id]

    event = create_shadow_event(
        event_type="QUOTE_ATTACHED_TO_LEAD",
        lead_id=lead_id,
        actor_type="system",
        actor_id="API",
        parent_hash=quote.shadow.audit_hash,
        correlation_id=quote.shadow.parent_hash,
        payload={"quote_id": quote_id},
        quote_id=quote_id
    )

    if lead_id not in lead_chains: lead_chains[lead_id] = []
    lead_chains[lead_id].append(event)

    # Update quote shadow to reflect it's attached
    quote.shadow.audit_hash = event["hash"]
    quote.shadow.event = "QUOTE_ATTACHED_TO_LEAD"

    return {"status": "attached", "audit_hash": event["hash"]}

@router.post("/{lead_id}/send-quote")
async def send_quote(lead_id: str, quote_id: str, actor_ctx: Dict):
    if quote_id not in bridge.quotes:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote = bridge.quotes[quote_id]

    if quote.lead_id != lead_id:
        raise HTTPException(status_code=403, detail=f"QUOTE_LEAD_MISMATCH: Quote {quote_id} belongs to lead {quote.lead_id}, not {lead_id}")

    if quote.status != QuoteStatus.VERIFIED:
        raise HTTPException(status_code=400, detail="UNVERIFIED_QUOTE_SEND_BLOCKED")

    if actor_ctx.get("actor_type") == "ai":
        raise HTTPException(status_code=403, detail="AI_QUOTE_SEND_FORBIDDEN")

    event = create_shadow_event(
        event_type="QUOTE_SENT_BY_HUMAN",
        lead_id=lead_id,
        actor_type="human",
        actor_id=actor_ctx["actor_id"],
        parent_hash=quote.shadow.audit_hash,
        correlation_id=quote.shadow.parent_hash,
        payload={"quote_id": quote_id},
        quote_id=quote_id
    )

    if lead_id not in lead_chains: lead_chains[lead_id] = []
    lead_chains[lead_id].append(event)

    # Update quote shadow to reflect it's sent
    quote.shadow.audit_hash = event["hash"]
    quote.shadow.event = "QUOTE_SENT_BY_HUMAN"

    return {"status": "sent", "audit_hash": event["hash"]}

@router.get("/{lead_id}/shadow-chain")
async def get_shadow_chain(lead_id: str):
    # Mocking a full chain for a known lead if it exists
    base_chain = [
        "DM_RECEIVED", "INTENT_CLASSIFIED", "LEAD_SCORED",
        "COMPLIANCE_CHECKED", "HUMAN_HANDOFF_CREATED",
        "FCE_QUOTE_REQUESTED"
    ]

    if lead_id in lead_chains:
        for event in lead_chains[lead_id]:
            base_chain.append(event["event_type"])

    return base_chain

@router.post("/{lead_id}/mark-won")
async def mark_won(lead_id: str, quote_id: str, booking_ref: str, revenue: float,
                   content_id: str, campaign_id: str, actor_id: str):

    if lead_id not in lead_chains or not lead_chains[lead_id]:
        raise HTTPException(status_code=400, detail="LEAD_CHAIN_NOT_FOUND: Cannot mark won without previous events")

    previous_event = lead_chains[lead_id][-1]

    event = create_shadow_event(
        event_type="BOOKING_WON",
        lead_id=lead_id,
        actor_type="human",
        actor_id=actor_id,
        parent_hash=previous_event["hash"],
        correlation_id=previous_event["correlation_id"],
        payload={"booking_ref": booking_ref, "revenue": revenue},
        quote_id=quote_id,
        content_id=content_id,
        campaign_id=campaign_id
    )

    lead_chains[lead_id].append(event)

    return {"status": "won", "audit_hash": event["hash"]}

@router.post("/{lead_id}/mark-lost")
async def mark_lost(lead_id: str, loss_reason: str, actor_id: str):
    if lead_id not in lead_chains or not lead_chains[lead_id]:
        raise HTTPException(status_code=400, detail="LEAD_CHAIN_NOT_FOUND: Cannot mark lost without previous events")

    previous_event = lead_chains[lead_id][-1]

    event = create_shadow_event(
        event_type="BOOKING_LOST",
        lead_id=lead_id,
        actor_type="human",
        actor_id=actor_id,
        parent_hash=previous_event["hash"],
        correlation_id=previous_event["correlation_id"],
        payload={"loss_reason": loss_reason}
    )

    lead_chains[lead_id].append(event)

    return {"status": "lost", "audit_hash": event["hash"]}
