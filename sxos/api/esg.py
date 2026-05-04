from fastapi import APIRouter
from sxos.esg.service import calculate_trip_esg

router = APIRouter(prefix="/sxos/esg")

@router.post("/calculate")
def calculate_esg(distance_km: float, weight_kg: float, transport_type: str = "vessel"):
    return calculate_trip_esg(distance_km, weight_kg, transport_type)

@router.get("/report")
def get_esg_report(tenant_id: str):
    return {"tenant_id": tenant_id, "score": 85.5, "co2_saved_kg": 1200.0}
