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
@governance.fail_closed_operation
def apollo_priority_override(journey_id: int, db: Session = Depends(get_ut_db)):
    """APOLLO Priority Override: No human delay allowed."""
    return {"status": "overridden", "journey_id": journey_id}

@router.get("/v1/availability", response_model=List[Any])
@governance.fail_closed_async_operation
async def query_availability(
    *,
    db: Session = Depends(get_ut_db),
    query: schemas.AvailabilityQuery = Depends(),
    authorization: str = Header(...),
    x_nexgen_patente: str = Header(...)
) -> Any:
    """
    Exposed API: Real-time availability.
    Mandatory: AEGIS validation via NEXUS.
    """
    # 1. AEGIS validation
    if not await nexus_client.verify_session(authorization.split(" ")[1], x_nexgen_patente):
        raise HTTPException(status_code=401, detail="AEGIS Verification Failed")

    return booking_service.get_availability(db, query=query)

@router.post("/v1/book", response_model=schemas.Journey)
@governance.fail_closed_async_operation
async def create_booking(
    *,
    db: Session = Depends(get_ut_db),
    booking_in: schemas.JourneyCreate,
    authorization: str = Header(...),
    x_nexgen_patente: str = Header(...)
) -> Any:
    """
    Exposed API: Single call for multi-leg journeys.
    Flow: AEGIS -> FCE -> UT Write -> SHADOW -> EVENTS
    """
    token = authorization.split(" ")[1]

    # 1. AEGIS Validation
    if not await nexus_client.verify_session(token, x_nexgen_patente):
        raise HTTPException(status_code=401, detail="AEGIS Trust Failed")

    # 2. FCE Preauth
    if not await nexus_client.preauthorize_payment(100.0, booking_in.trace_id):
        raise HTTPException(status_code=402, detail="FCE Preauth Failed")

    # 2.5 Scale Lock Enforcement
    if pulse_service.is_scale_locked(db):
        raise HTTPException(status_code=429, detail="Sovereign Scale Lock: GAN-50 Targets Not Met")

    # 3. Execute UT Write
    journey = booking_service.create_journey(db, obj_in=booking_in, actor="PARTNER")

    # 4. SHADOW commit
    await nexus_client.commit_evidence(booking_in.trace_id, {"action": "EXTERNAL_BOOKING", "journey_id": journey.id})

    # 5. EVENTS publish
    await nexus_client.publish_event("ut_journey_created", {"journey_id": journey.id, "trace_id": booking_in.trace_id})

    return journey

@router.post("/v1/cargo/create")
@governance.fail_closed_operation
def create_cargo_transfer(
    *,
    db: Session = Depends(get_ut_db),
    # obj_in: schemas.CargoCreate,
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
