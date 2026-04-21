from fastapi import APIRouter, HTTPException, Request
from .models import Flight
from .service import AirportService
from typing import List
from unified_suite.core.eleone import ELEONE

router = APIRouter()
service = AirportService()

@router.post("/flights", response_model=Flight)
async def create_flight(flight: Flight, request: Request):
    patente = request.headers.get("X-NexGen-Patente")

    try:
        scheduled_flight = ELEONE.execute(
            action="SCHEDULE_FLIGHT",
            subject_id=flight.flight_number,
            func=service.schedule_flight,
            args=[flight],
            constraints=["AEGIS", "MOATS"],
            patente_token=patente,
            tax_base=1500.00
        )
        return scheduled_flight
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=403 if isinstance(e, PermissionError) else 400, detail=str(e))

@router.get("/flights", response_model=List[Flight])
async def list_flights():
    return service.get_all_flights()

@router.post("/flights/{flight_number}/assign-gate")
async def assign_gate(flight_number: str, request: Request):
    patente = request.headers.get("X-NexGen-Patente")

    try:
        gate = ELEONE.execute(
            action="ASSIGN_GATE",
            subject_id=flight_number,
            func=service.assign_gate,
            args=[flight_number],
            constraints=["AEGIS", "MOATS"],
            patente_token=patente,
            tax_base=250.00
        )
        return {"flight_number": flight_number, "gate": gate}
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=403 if isinstance(e, PermissionError) else 400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
