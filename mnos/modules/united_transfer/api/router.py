from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Any

from mnos.core.api import deps
from mnos.modules.united_transfer import schemas, models
from mnos.modules.united_transfer.services import booking_service, telemetry_service

router = APIRouter()

@router.post("/bookings", response_model=schemas.Journey)
def create_multi_leg_booking(
    *,
    db: Session = Depends(deps.get_db),
    booking_in: schemas.JourneyCreate,
    current_user = Depends(deps.get_current_user)
) -> schemas.Journey:
    """
    SUPER API: Single call for multi-leg journeys.
    """
    return booking_service.create_journey(db, obj_in=booking_in, actor=current_user.email)

@router.get("/availability", response_model=List[Any])
def query_availability(
    *,
    db: Session = Depends(deps.get_db),
    query: schemas.AvailabilityQuery = Depends(),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """
    SUPER API: Real-time availability across ALL modes.
    """
    return booking_service.get_availability(db, query=query)

@router.post("/telemetry")
def report_telemetry(
    *,
    db: Session = Depends(deps.get_db),
    telemetry_in: schemas.TelemetryCreate,
    background_tasks: BackgroundTasks
) -> Any:
    """
    SUPER API: GPS telemetry and 'Safe Arrival' webhooks.
    """
    return telemetry_service.process_telemetry(db, obj_in=telemetry_in, background_tasks=background_tasks)
