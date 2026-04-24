from fastapi import APIRouter
from sxos.metrics.service import track_economic_metrics

router = APIRouter(prefix="/sxos/metrics")

@router.get("/gmv")
def get_gmv():
    return {"gmv": 1250000.0, "currency": "USD"}

@router.get("/yield")
def get_system_yield():
    return {"system_yield": 0.12, "period": "current_quarter"}

@router.get("/distribution")
def get_distribution():
    return {"government": 0.17, "suppliers": 0.65, "logistics": 0.10, "system": 0.08}
