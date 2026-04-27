from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mnos.core.db.session import get_db
from mnos.core.security.guard import guard
from mnos.modules.flight_mvp.services.engine import flight_mvp_engine
from typing import Any, Dict

router = APIRouter()

@router.post("/sessions")
async def create_session(
    *,
    db: Session = Depends(get_db),
    data: Dict[str, Any]
) -> Any:
    ctx = {"trace_id": f"FLT-{data['flight_number']}", "aegis_id": "DMC_PARTNER"}
    return await guard.execute_sovereign_action_async(
        "FLIGHT_MVP_SESSION_CREATE",
        ctx,
        flight_mvp_engine.create_mvp_session,
        db,
        **data
    )

@router.post("/poll/{session_id}")
async def trigger_poll(
    session_id: int,
    db: Session = Depends(get_db)
) -> Any:
    ctx = {"trace_id": f"POLL-{session_id}", "aegis_id": "SYSTEM_CRON"}
    return await guard.execute_sovereign_action_async(
        "FLIGHT_MVP_POLL",
        ctx,
        flight_mvp_engine.check_for_delays,
        db,
        session_id=session_id
    )
