from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

class BookingIntentRequest(BaseModel):
    booking_ref: str
    room_type_id: str
    check_in: str
    check_out: str
    total_amount: float
    trace_id: str

class PaymentConfirmation(BaseModel):
    payment_ref: str
    amount: float

def create_booking_gate_router(engine, get_actor_ctx):
    router = APIRouter(tags=["imoxon.booking_gate"])

    @router.post("/gate/ingest")
    async def ingest_intent(req: BookingIntentRequest, actor: dict = Depends(get_actor_ctx)):
        """iMOXON Booking Gate: Ingest intent from Prestige."""
        actor["trace_id"] = req.trace_id
        return engine.ingest_booking_intent(actor, req.model_dump())

    @router.post("/gate/{booking_id}/confirm")
    async def confirm_booking(booking_id: str, pay: PaymentConfirmation, actor: dict = Depends(get_actor_ctx)):
        """iMOXON Booking Gate: Confirm with UPOS payment."""
        # Use existing booking state to find trace_id
        booking = engine.booking_states.get(booking_id)
        if booking: actor["trace_id"] = booking["trace_id"]

        return engine.confirm_booking(actor, booking_id, pay.payment_ref, pay.amount)

    @router.post("/gate/{booking_id}/execute")
    async def request_execution(booking_id: str, actor: dict = Depends(get_actor_ctx)):
        """iMOXON Booking Gate: Transition to execution pending."""
        booking = engine.booking_states.get(booking_id)
        if booking: actor["trace_id"] = booking["trace_id"]

        return engine.request_execution(actor, booking_id)

    @router.post("/gate/{booking_id}/complete")
    async def complete_execution(booking_id: str, signal: dict, actor: dict = Depends(get_actor_ctx)):
        """iMOXON Booking Gate: Final reality check and completion."""
        booking = engine.booking_states.get(booking_id)
        if booking: actor["trace_id"] = booking["trace_id"]

        return engine.complete_execution(actor, booking_id, signal)

    @router.get("/gate/{booking_id}/audit")
    async def get_audit_trail(booking_id: str):
        """iMOXON Booking Gate: Export Merkle trace chain."""
        audit = engine.final_audit_check(booking_id)
        if not audit:
            raise HTTPException(status_code=404, detail="Booking not found")
        return audit

    return router
