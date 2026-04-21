from fastapi import APIRouter, HTTPException, Request
from .models import Vessel, Container
from .service import SeaPortService
from typing import List
from unified_suite.core.eleone import ELEONE

router = APIRouter()
service = SeaPortService()

@router.post("/vessels", response_model=Vessel)
async def register_vessel(vessel: Vessel, request: Request):
    patente = request.headers.get("X-NexGen-Patente")

    try:
        registered_vessel = ELEONE.execute(
            action="REGISTER_VESSEL",
            subject_id=vessel.vessel_id,
            func=service.register_vessel,
            args=[vessel],
            constraints=["AEGIS", "MOATS"],
            patente_token=patente,
            tax_base=5000.00
        )
        return registered_vessel
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=403 if isinstance(e, PermissionError) else 400, detail=str(e))

@router.get("/vessels", response_model=List[Vessel])
async def list_vessels():
    return service.get_all_vessels()

@router.post("/vessels/{vessel_id}/assign-berth")
async def assign_berth(vessel_id: str, request: Request):
    patente = request.headers.get("X-NexGen-Patente")

    try:
        berth = ELEONE.execute(
            action="ASSIGN_BERTH",
            subject_id=vessel_id,
            func=service.assign_berth,
            args=[vessel_id],
            constraints=["AEGIS", "MOATS"],
            patente_token=patente,
            tax_base=750.00
        )
        return {"vessel_id": vessel_id, "berth": berth}
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=403 if isinstance(e, PermissionError) else 400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/vessels/{vessel_id}/manifest", response_model=List[Container])
async def get_manifest(vessel_id: str):
    return service.get_vessel_manifest(vessel_id)
