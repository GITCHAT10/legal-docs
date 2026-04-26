from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import List, Any
import uuid
from united_transfer_system.db_session import get_ut_db
from united_transfer_system import schemas, models
from united_transfer_system.services import booking_service, journey_service
from mnos.core.security.guard import guard

router = APIRouter()

@router.get("/v1/availability", response_model=List[Any])
async def query_availability(
    *,
    db: Session = Depends(get_ut_db),
    query: schemas.AvailabilityQuery = Depends()
) -> Any:
    return booking_service.get_availability(db, query=query)

@router.post("/v1/book", response_model=schemas.Journey)
async def create_booking(
    *,
    db: Session = Depends(get_ut_db),
    booking_in: schemas.JourneyCreate,
    x_device_id: str = Header(...)
) -> Any:
    ctx = {
        "trace_id": booking_in.trace_id,
        "aegis_id": "VERIFIED_PARTNER",
        "device_id": x_device_id
    }
    return await guard.execute_sovereign_action_async(
        "UT_BOOKING_CREATE",
        ctx,
        booking_service.create_journey,
        db,
        obj_in=booking_in,
        ctx=ctx
    )

@router.post("/v1/telemetry")
async def record_telemetry(
    *,
    db: Session = Depends(get_ut_db),
    telemetry_in: schemas.TelemetryCreate
) -> Any:
    ctx = {
        "trace_id": f"TEL-{telemetry_in.leg_id}-{uuid.uuid4().hex[:4]}",
        "aegis_id": "SYSTEM_DEVICE",
    }
    return guard.execute_sovereign_action(
        "UT_TELEMETRY_INGEST",
        ctx,
        journey_service.process_telemetry,
        db,
        leg_id=telemetry_in.leg_id,
        lat=telemetry_in.latitude,
        lon=telemetry_in.longitude,
        speed=telemetry_in.speed
    )

@router.post("/v1/handshake")
async def verify_handshake(
    *,
    db: Session = Depends(get_ut_db),
    handshake: schemas.HandshakeInput
) -> Any:
    ctx = {
        "trace_id": f"HS-{handshake.leg_id}",
        "aegis_id": handshake.actor_id,
    }
    success = guard.execute_sovereign_action(
        "UT_HANDSHAKE_VERIFY",
        ctx,
        journey_service.verify_handshake,
        db,
        leg_id=handshake.leg_id,
        scan_type=handshake.scan_type,
        master_code=handshake.master_code,
        actor_id=handshake.actor_id,
        actor_role=handshake.actor_role
    )
    if not success:
        raise HTTPException(status_code=400, detail="Invalid handshake or master code")
    return {"status": "success"}

@router.get("/v1/partners/payouts")
async def list_payouts(
    *,
    db: Session = Depends(get_ut_db),
    owner_id: str
) -> Any:
    wallet = db.query(models.Wallet).filter(models.Wallet.owner_id == owner_id).first()
    if not wallet:
        return []
    return wallet.transactions
