from fastapi import APIRouter, Depends, HTTPException, Header
from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel

class CreateReservationRequest(BaseModel):
    guest_id: str
    room_type_id: str
    rate_plan_id: str
    check_in: date
    check_out: date
    idempotency_key: str
    total_amount: float

def create_pms_router(booking_logic, availability_engine, get_actor_ctx):
    router = APIRouter(tags=["pms"])

    @router.post("/reservations")
    async def create_reservation(req: CreateReservationRequest, actor: dict = Depends(get_actor_ctx)):
        """PMS: Create new reservation (DRAFT -> CONFIRMED)."""
        try:
            return booking_logic.create_reservation(actor, req.model_dump())
        except ValueError as e:
            if "CONFLICT" in str(e):
                raise HTTPException(status_code=409, detail=str(e))
            raise HTTPException(status_code=422, detail=str(e))

    @router.get("/availability")
    async def check_availability(
        check_in: date,
        check_out: date,
        room_type_id: str,
        actor: dict = Depends(get_actor_ctx)
    ):
        """PMS: Check inventory availability."""
        count = availability_engine.get_availability(room_type_id, check_in, check_out)
        return {"available_rooms": count, "room_type_id": room_type_id}

    @router.post("/reservations/{res_id}/cancel")
    async def cancel_reservation(res_id: str, reason: str = "guest_request", actor: dict = Depends(get_actor_ctx)):
        """PMS: Cancel confirmed reservation."""
        try:
            return booking_logic.cancel_reservation(actor, res_id, reason)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    return router
