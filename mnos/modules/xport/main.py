from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from mnos.modules.xport.service import orchestrator

router = APIRouter(prefix="/mnos/xport/v2", tags=["XPORT v2"])

class TransportRequest(BaseModel):
    subject_id: str
    action: str
    pax: int = 0
    nights: int = 0
    metadata: Optional[dict] = {}

@router.post("/execute")
async def execute_xport_action(
    req: TransportRequest,
    x_request_id: str = Header(...),
    x_nexgen_patente: str = Header(...)
):
    """
    Unified National Transport Execution Point.
    Handles Airport (GATE) and Seaport (BERTH) orchestration.
    """
    try:
        result = orchestrator.execute_sovereign_action(
            trace_id=x_request_id,
            action=req.action,
            subject_id=req.subject_id,
            patente_token=x_nexgen_patente,
            payload=req.model_dump()
        )
        return {"success": True, "data": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sovereign Execution Error: {str(e)}")

@router.post("/release")
async def release_xport_resource(
    subject_id: str,
    action: str, # e.g., RELEASE_GATE, RELEASE_BERTH
    x_nexgen_patente: str = Header(...)
):
    # Release logic simplified for sim
    success = orchestrator.release_resource(action, subject_id)
    return {"success": success, "subject_id": subject_id}

@router.get("/status")
async def get_national_grid_status():
    return {
        "airport_gates": orchestrator.airport_assets,
        "seaport_berths": orchestrator.seaport_assets
    }
