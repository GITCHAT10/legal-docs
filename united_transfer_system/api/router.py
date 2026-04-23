from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header, Request
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from united_transfer_system.db_session import get_ut_db
from united_transfer_system import schemas, models
from united_transfer_system.services import booking_service, telemetry_service, governance, pulse, trust_lock, apollo_engine, valuation
from united_transfer_system.integrations.nexus_client import nexus_client

router = APIRouter()

@router.get("/v1/pulse", response_model=Any)
def get_pulse_metrics(db: Session = Depends(get_ut_db)):
    return pulse_service.get_current_metrics(db)

@router.get("/v1/trust/{partner_id}")
def get_partner_trust(partner_id: int, db: Session = Depends(get_ut_db)):
    partner = db.query(models.Partner).filter(models.Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return partner

@router.post("/v1/apollo/override")
def apollo_priority_override(journey_id: int, db: Session = Depends(get_ut_db)):
    """APOLLO Priority Override."""
    return {"status": "overridden", "journey_id": journey_id}

@router.get("/v1/availability", response_model=List[Any])
async def query_availability(
    *,
    db: Session = Depends(get_ut_db),
    query: schemas.AvailabilityQuery = Depends(),
    authorization: str = Header(...),
    x_nexgen_patente: str = Header(...)
) -> Any:
    """
    Exposed API: Real-time availability.
    """
    ctx = {"trace_id": "AVAIL-QUERY", "aegis_id": "PARTNER"} # Minimal ctx for read
    return booking_service.get_availability(db, query=query)

@router.post("/v1/book", response_model=schemas.Journey)
async def create_booking(
    *,
    db: Session = Depends(get_ut_db),
    booking_in: schemas.JourneyCreate,
    authorization: str = Header(...),
    x_nexgen_patente: str = Header(...),
    x_device_id: str = Header(...)
) -> Any:
    """
    Exposed API: Atomic Journey Creation.
    Flow: AEGIS -> FCE -> UT Write -> SHADOW -> EVENTS
    """
    ctx = {
        "trace_id": booking_in.trace_id,
        "aegis_id": "VERIFIED_PARTNER", # Mocked AEGIS result
        "device_id": x_device_id
    }

    # Execution handled by booking_service wrapped in ExecutionGuard
    return booking_service.create_journey(db, obj_in=booking_in, ctx=ctx)

@router.post("/v1/journey/{journey_id}/verify-pickup")
async def verify_pickup(
    journey_id: int,
    leg_id: int,
    scan_data: str,
    db: Session = Depends(get_ut_db),
    authorization: str = Header(...),
    x_nexgen_patente: str = Header(...),
    x_trace_id: str = Header(...)
):
    ctx = {"trace_id": x_trace_id, "aegis_id": "OPERATOR"}
    return booking_service.verify_handshake(db, leg_id=leg_id, qr_type="QR1", scan_data=scan_data, ctx=ctx)

@router.post("/v1/journey/{journey_id}/verify-drop")
async def verify_drop(
    journey_id: int,
    leg_id: int,
    scan_data: str,
    db: Session = Depends(get_ut_db),
    authorization: str = Header(...),
    x_nexgen_patente: str = Header(...),
    x_trace_id: str = Header(...)
):
    ctx = {"trace_id": x_trace_id, "aegis_id": "OPERATOR"}
    return booking_service.verify_handshake(db, leg_id=leg_id, qr_type="QR2", scan_data=scan_data, ctx=ctx)

@router.post("/v1/journey/{journey_id}/payout")
async def execute_payout(
    journey_id: int,
    db: Session = Depends(get_ut_db),
    authorization: str = Header(...),
    x_trace_id: str = Header(...)
):
    ctx = {"trace_id": x_trace_id, "aegis_id": "SYSTEM_FINANCE"}
    return await booking_service.release_payment(db, journey_id=journey_id, ctx=ctx)

@router.post("/v1/cargo/create")
def create_cargo_transfer(
    *,
    db: Session = Depends(get_ut_db),
    authorization: str = Header(...)
) -> Any:
    return {"status": "accepted", "type": "cargo"}

@router.get("/v1/tracking/{id}")
def get_tracking(
    id: int,
    db: Session = Depends(get_ut_db)
) -> Any:
    return {"id": id, "status": "in_transit", "last_gps": {"lat": 4.1, "lon": 73.5}}

@router.post("/telemetry")
def report_telemetry(
    *,
    db: Session = Depends(get_ut_db),
    telemetry_in: schemas.TelemetryCreate,
    background_tasks: BackgroundTasks
) -> Any:
    return telemetry_service.process_telemetry(db, obj_in=telemetry_in, background_tasks=background_tasks)
