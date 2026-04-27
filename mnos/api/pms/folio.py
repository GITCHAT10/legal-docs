from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ChargeRequest(BaseModel):
    folio_id: str
    category: str = "ROOM"
    description: str
    amount: float
    pax_count: int = 0
    nights: int = 0
    geo_location: Optional[Dict[str, float]] = None

class ReversalRequest(BaseModel):
    charge_id: str
    reason_code: str
    approver_id: str

class PaymentRequest(BaseModel):
    folio_id: str
    amount: float
    method: str # CASH, CARD, WALLET

def create_folio_router(folio_logic, get_actor_ctx):
    router = APIRouter(tags=["pms-folio"])

    @router.get("/guest/{guest_id}")
    async def get_folio_by_guest(guest_id: str, actor: dict = Depends(get_actor_ctx)):
        """PMS: Fetch or create folio for guest."""
        folio = folio_logic.get_or_create_folio(guest_id)
        return folio.to_dict()

    @router.get("/{folio_id}")
    async def get_folio(folio_id: str, actor: dict = Depends(get_actor_ctx)):
        """PMS: Fetch folio by ID."""
        folio = folio_logic.folios.get(folio_id)
        if not folio:
            raise HTTPException(status_code=404, detail="Folio not found")
        return folio.to_dict()

    @router.post("/charge")
    async def post_charge(req: ChargeRequest, actor: dict = Depends(get_actor_ctx)):
        """PMS: Post a charge to a folio."""
        try:
            return folio_logic.post_charge(actor, req.folio_id, req.model_dump())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/charge/reversal")
    async def reverse_charge(req: ReversalRequest, actor: dict = Depends(get_actor_ctx)):
        """PMS: Reverse a posted charge (Immutable Negative Entry)."""
        try:
            return folio_logic.reverse_charge(actor, req.charge_id, req.reason_code, req.approver_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.post("/payment")
    async def process_payment(req: PaymentRequest, actor: dict = Depends(get_actor_ctx)):
        """PMS: Process partial or full payment."""
        try:
            return folio_logic.process_payment(actor, req.folio_id, req.model_dump())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router
