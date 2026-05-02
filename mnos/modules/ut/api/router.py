from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, List, Optional
from decimal import Decimal

def create_ut_router(booking_engine, route_engine, fce_split, boarding_service, sync_service, safety_gate, get_actor_ctx):
    router = APIRouter(prefix="/ut", tags=["UT_PPMC"])

    # --- Identity & Vendors ---
    @router.post("/identity/login")
    async def ut_login(actor: dict = Depends(get_actor_ctx)):
        return {"status": "AUTHENTICATED", "actor": actor}

    @router.get("/vendors/{vendor_id}/manifest/live")
    async def get_live_manifest(vendor_id: str, actor: dict = Depends(get_actor_ctx)):
        # Role check for manifest access
        if actor["role"] not in ["SUPPLIER_ADMIN", "UT_COMMAND"]:
            raise HTTPException(status_code=403, detail="ROLE_CLAIM_REQUIRED: Access Denied")
        return {"vendor_id": vendor_id, "manifest": "LIVE_DATA_STUB"}

    # --- Routes & Journeys ---
    @router.post("/routes/search")
    async def search_routes(origin: str, destination: str, actor: dict = Depends(get_actor_ctx)):
        return route_engine.search_routes(origin, destination)

    @router.post("/journeys/mixed-route")
    async def mixed_route(origin: str, destination: str, actor: dict = Depends(get_actor_ctx)):
        return route_engine.calculate_mixed_journey(origin, destination)

    # --- Bookings ---
    @router.post("/bookings/intent")
    async def booking_intent(data: dict, x_aegis_device: str = Header(None, alias="X-AEGIS-DEVICE"), actor: dict = Depends(get_actor_ctx)):
        try:
            # Inject device_id into actor for ExecutionGuard
            actor["device_id"] = x_aegis_device
            return booking_engine.create_intent(actor, data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/bookings/confirm")
    async def booking_confirm(booking_id: str, x_aegis_device: str = Header(None, alias="X-AEGIS-DEVICE"), actor: dict = Depends(get_actor_ctx)):
        actor["device_id"] = x_aegis_device
        return booking_engine.confirm_booking(actor, booking_id)

    # --- Finance & FCE ---
    @router.post("/fce/quote")
    async def fce_quote(trace_id: str, amount: float, actor: dict = Depends(get_actor_ctx)):
        return fce_split.create_quote(trace_id, Decimal(str(amount)))

    @router.post("/fce/payout/release")
    async def release_payout(quote_id: str, orca: bool, shadow: bool, apollo: bool, x_aegis_device: str = Header(None, alias="X-AEGIS-DEVICE"), actor: dict = Depends(get_actor_ctx)):
        try:
            actor["device_id"] = x_aegis_device
            return fce_split.release_payout(actor, quote_id, orca, shadow, apollo)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

    # --- ORCA Boarding ---
    @router.post("/orca/qr-scan")
    async def qr_scan(qr_token: str, actor: dict = Depends(get_actor_ctx)):
        try:
            return boarding_service.validate_qr_scan(actor, qr_token)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # --- APOLLO Sync ---
    @router.post("/apollo/sync/replay")
    async def apollo_replay(actor: dict = Depends(get_actor_ctx)):
        return sync_service.replay_sync()

    # --- Safety Gate ---
    @router.post("/safety/check")
    async def safety_check(asset_id: str, actor: dict = Depends(get_actor_ctx)):
        # Mock data for check
        asset_data = {"capacity": 20, "passenger_count": 10, "captain_status": "VERIFIED", "lifejacket_count": 20, "insurance_expiry": "2026-01-01"}
        weather_data = {"sea_state": 1}
        return safety_gate.validate_dispatch(actor, asset_data, weather_data)

    return router
