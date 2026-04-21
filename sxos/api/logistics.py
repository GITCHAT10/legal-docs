from fastapi import APIRouter
from sxos.logistics.service import optimize_route

router = APIRouter(prefix="/sxos/logistics")

@router.post("/route_optimize")
def route_optimize(origin: str, destination: str, load_kg: float):
    return optimize_route(origin, destination, load_kg)

@router.get("/return_match")
def return_match(vessel_id: str, location: str):
    return {"match_found": True, "cargo": "Waste Plastic", "vessel_id": vessel_id}
