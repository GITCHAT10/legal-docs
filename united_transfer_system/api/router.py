from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import List, Any
from united_transfer_system.db_session import get_ut_db
from united_transfer_system import schemas, models
from united_transfer_system.services import booking_service

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
    return await booking_service.create_journey(db, obj_in=booking_in, ctx=ctx)
