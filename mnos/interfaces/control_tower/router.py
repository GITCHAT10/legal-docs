from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import List, Any
from mnos.core.db.session import get_db
from mnos.modules.ut_core.schemas import journey as schemas
from mnos.modules.ut_core.services import journey_service
from mnos.interfaces.control_tower.views import router as views_router

router = APIRouter()
router.include_router(views_router, prefix="/ui")

@router.get("/availability", response_model=List[Any])
async def query_availability(
    *,
    db: Session = Depends(get_db),
    query: schemas.AvailabilityQuery = Depends(),
    authorization: str = Header(...)
) -> Any:
    return [
        {"type": "land", "provider": "Taxi-01", "price": 150.0},
        {"type": "air", "provider": "IAS-ATR72", "price": 2500.0},
        {"type": "sea", "provider": "Speedboat-X", "price": 500.0}
    ]

@router.post("/book", response_model=schemas.Journey)
async def create_booking(
    *,
    db: Session = Depends(get_db),
    booking_in: schemas.JourneyCreate,
    x_device_id: str = Header(...)
) -> Any:
    ctx = {
        "trace_id": booking_in.trace_id,
        "aegis_id": "VERIFIED_PARTNER",
        "device_id": x_device_id
    }
    return await journey_service.create_journey(db, obj_in=booking_in, ctx=ctx)
