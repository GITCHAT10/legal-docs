from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mnos.core.db.session import get_db
from mnos.core.security.guard import guard
from mnos.modules.boat_ops.services import services
from typing import Any, Dict

router = APIRouter()

@router.post("/crew/shifts/assign")
def assign_shift(
    *,
    db: Session = Depends(get_db),
    data: Dict[str, Any],
    actor_id: str = "ORCA_DISPATCHER"
) -> Any:
    ctx = {"trace_id": f"SHIFT-{data['crew_id']}", "aegis_id": actor_id}
    return guard.execute_sovereign_action(
        "BOAT_OPS_SHIFT_ASSIGN",
        ctx,
        services.crew_service.assign_shift,
        db,
        crew_id=data['crew_id'],
        vessel_id=data['vessel_id'],
        start=data['start'],
        end=data['end']
    )

@router.post("/fuel/log")
def log_fuel(
    *,
    db: Session = Depends(get_db),
    data: Dict[str, Any]
) -> Any:
    ctx = {"trace_id": f"FUEL-{data['vessel_id']}", "aegis_id": "CREW_APP"}
    return guard.execute_sovereign_action(
        "BOAT_OPS_FUEL_LOG",
        ctx,
        services.fuel_service.log_fuel,
        db,
        vessel_id=data['vessel_id'],
        liters=data['liters'],
        atoll=data['atoll'],
        logged_by=data['crew_id']
    )
