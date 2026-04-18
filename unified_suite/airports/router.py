from fastapi import APIRouter, HTTPException
from .models import Flight
from .service import AirportService
from typing import List

router = APIRouter()
service = AirportService()

@router.post("/flights", response_model=Flight)
async def create_flight(flight: Flight):
    return service.schedule_flight(flight)

@router.get("/flights", response_model=List[Flight])
async def list_flights():
    return service.get_all_flights()

@router.post("/flights/{flight_number}/assign-gate")
async def assign_gate(flight_number: str):
    gate = service.assign_gate(flight_number)
    if not gate:
        raise HTTPException(status_code=404, detail="Flight not found or no gates available")
    return {"flight_number": flight_number, "gate": gate}
