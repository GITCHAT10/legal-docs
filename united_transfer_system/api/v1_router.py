from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Any
import uuid
from united_transfer_system.db_session import get_ut_db
from united_transfer_system import schemas, models
from united_transfer_system.services import booking_service, journey_service
from mnos.core.security.guard import guard

# Universal API Sub-Routers
partner_router = APIRouter(prefix="/partners", tags=["Partners"])
transfer_router = APIRouter(prefix="/transfer", tags=["Transfer"])
journey_router = APIRouter(prefix="/journey", tags=["Journey"])
asset_router = APIRouter(prefix="/assets", tags=["Assets"])
gps_router = APIRouter(prefix="/gps", tags=["GPS"])
execution_router = APIRouter(prefix="/execution", tags=["Execution"])
finance_router = APIRouter(prefix="/finance", tags=["Finance"])

# --- Partner API ---
@partner_router.post("/register")
async def register_partner(partner_in: schemas.PartnerCreate, db: Session = Depends(get_ut_db)):
    return await booking_service.create_partner(db, obj_in=partner_in)

# --- Transfer API ---
@transfer_router.post("/request")
async def request_transfer(request_in: schemas.TransferRequest, db: Session = Depends(get_ut_db)):
    return await booking_service.process_transfer_request(db, obj_in=request_in)

# --- Journey API ---
@journey_router.post("/quote")
async def quote_journey(query: schemas.AvailabilityQuery, db: Session = Depends(get_ut_db)):
    return booking_service.get_availability(db, query=query)

@journey_router.post("/confirm")
async def confirm_journey(booking_in: schemas.JourneyCreate, db: Session = Depends(get_ut_db), x_device_id: str = Header(...)):
    ctx = {"trace_id": booking_in.trace_id, "aegis_id": "VERIFIED_PARTNER", "device_id": x_device_id}
    return await guard.execute_sovereign_action_async("UT_BOOKING_CONFIRM", ctx, booking_service.create_journey, db, obj_in=booking_in, ctx=ctx)

# --- Asset API ---
@asset_router.post("/vessels/sync")
async def sync_vessels(vessels: List[schemas.AssetSync], db: Session = Depends(get_ut_db)):
    return {"status": "synced", "count": len(vessels)}

# --- GPS API ---
@gps_router.post("/location")
async def record_location(telemetry_in: schemas.TelemetryCreate, db: Session = Depends(get_ut_db)):
    ctx = {"trace_id": f"TEL-{telemetry_in.leg_id}", "aegis_id": "GPS_PROVIDER"}
    return guard.execute_sovereign_action("UT_GPS_INGEST", ctx, journey_service.process_telemetry, db, **telemetry_in.dict())

# --- Execution API ---
@execution_router.post("/boarding-confirm")
async def confirm_boarding(handshake: schemas.HandshakeInput, db: Session = Depends(get_ut_db)):
    ctx = {"trace_id": f"HS-BOARD-{handshake.leg_id}", "aegis_id": handshake.actor_id}
    return guard.execute_sovereign_action("UT_BOARDING_CONFIRM", ctx, journey_service.verify_handshake, db, **handshake.dict())

@execution_router.post("/arrival-confirm")
async def confirm_arrival(leg_id: int, db: Session = Depends(get_ut_db)):
    return await journey_service.confirm_arrival(db, leg_id=leg_id)

# --- Finance API ---
@finance_router.post("/payout")
async def trigger_payout(leg_id: int, db: Session = Depends(get_ut_db)):
    return await journey_service.process_payout(db, leg_id=leg_id)

# Master Router
api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(partner_router)
api_v1_router.include_router(transfer_router)
api_v1_router.include_router(journey_router)
api_v1_router.include_router(asset_router)
api_v1_router.include_router(gps_router)
api_v1_router.include_router(execution_router)
api_v1_router.include_router(finance_router)
