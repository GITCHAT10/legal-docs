from fastapi import APIRouter, HTTPException, Request
from .models import Flight
from .service import AirportService
from typing import List
import requests
import os

router = APIRouter()
service = AirportService()

MNOS_URL = os.getenv("MNOS_URL", "http://localhost:8000")

@router.post("/flights", response_model=Flight)
async def create_flight(flight: Flight, request: Request):
    # 1. Register flight locally
    scheduled_flight = service.schedule_flight(flight)

    # 2. Assign Gate via XPORT v2 (National Orchestrator)
    headers = {
        "X-Request-ID": request.headers.get("X-Request-ID", "req_sim"),
        "X-NexGen-Patente": request.headers.get("X-NexGen-Patente"),
        "Content-Type": "application/json"
    }

    xport_req = {
        "subject_id": flight.flight_number,
        "action": "ASSIGN_GATE",
        "pax": 150, # Example pax for tax calculation
        "nights": 1
    }

    resp = requests.post(f"{MNOS_URL}/mnos/xport/v2/execute", json=xport_req, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json().get("detail", "XPORT Failure"))

    xport_data = resp.json().get("data")
    scheduled_flight.gate = xport_data.get("asset")

    return scheduled_flight

@router.get("/flights", response_model=List[Flight])
async def list_flights():
    return service.get_all_flights()

@router.post("/flights/{flight_number}/assign-gate")
async def assign_gate(flight_number: str, request: Request):
    # Delegate to MNOS XPORT v2
    headers = {
        "X-Request-ID": request.headers.get("X-Request-ID", "req_sim_manual"),
        "X-NexGen-Patente": request.headers.get("X-NexGen-Patente"),
        "Content-Type": "application/json"
    }

    xport_req = {
        "subject_id": flight_number,
        "action": "ASSIGN_GATE"
    }

    resp = requests.post(f"{MNOS_URL}/mnos/xport/v2/execute", json=xport_req, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json().get("detail", "XPORT Failure"))

    return resp.json().get("data")
