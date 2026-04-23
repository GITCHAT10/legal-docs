from fastapi import APIRouter, HTTPException, Request
from .models import Vessel, Container
from .service import SeaPortService
from typing import List
import requests
import os

router = APIRouter()
service = SeaPortService()

MNOS_URL = os.getenv("MNOS_URL", "http://localhost:8000")

@router.post("/vessels", response_model=Vessel)
async def register_vessel(vessel: Vessel, request: Request):
    # 1. Register vessel locally
    registered_vessel = service.register_vessel(vessel)

    # 2. Assign Berth via XPORT v2 (National Orchestrator)
    headers = {
        "X-Request-ID": request.headers.get("X-Request-ID", "req_sim_port"),
        "X-NexGen-Patente": request.headers.get("X-NexGen-Patente"),
        "Content-Type": "application/json"
    }

    xport_req = {
        "subject_id": vessel.vessel_id,
        "action": "ASSIGN_BERTH",
        "pax": 0,
        "nights": 0
    }

    resp = requests.post(f"{MNOS_URL}/mnos/xport/v2/execute", json=xport_req, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json().get("detail", "XPORT Failure"))

    xport_data = resp.json().get("data")
    registered_vessel.berth = xport_data.get("asset")
    registered_vessel.status = "DOCKED"

    return registered_vessel

@router.get("/vessels", response_model=List[Vessel])
async def list_vessels():
    return service.get_all_vessels()

@router.post("/vessels/{vessel_id}/assign-berth")
async def assign_berth(vessel_id: str, request: Request):
    # Delegate to MNOS XPORT v2
    headers = {
        "X-Request-ID": request.headers.get("X-Request-ID", "req_sim_port_manual"),
        "X-NexGen-Patente": request.headers.get("X-NexGen-Patente"),
        "Content-Type": "application/json"
    }

    xport_req = {
        "subject_id": vessel_id,
        "action": "ASSIGN_BERTH"
    }

    resp = requests.post(f"{MNOS_URL}/mnos/xport/v2/execute", json=xport_req, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json().get("detail", "XPORT Failure"))

    return resp.json().get("data")

@router.get("/vessels/{vessel_id}/manifest", response_model=List[Container])
async def get_manifest(vessel_id: str):
    return service.get_vessel_manifest(vessel_id)
