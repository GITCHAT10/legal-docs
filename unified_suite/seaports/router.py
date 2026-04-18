from fastapi import APIRouter, HTTPException
from .models import Vessel, Container
from .service import SeaPortService
from typing import List

router = APIRouter()
service = SeaPortService()

@router.post("/vessels", response_model=Vessel)
async def register_vessel(vessel: Vessel):
    return service.register_vessel(vessel)

@router.get("/vessels", response_model=List[Vessel])
async def list_vessels():
    return service.get_all_vessels()

@router.post("/vessels/{vessel_id}/assign-berth")
async def assign_berth(vessel_id: str):
    berth = service.assign_berth(vessel_id)
    if not berth:
        raise HTTPException(status_code=404, detail="Vessel not found or no berths available")
    return {"vessel_id": vessel_id, "berth": berth}

@router.get("/vessels/{vessel_id}/manifest", response_model=List[Container])
async def get_manifest(vessel_id: str):
    return service.get_vessel_manifest(vessel_id)
