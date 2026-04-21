from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mnos.core.api import deps
from mnos.modules.shadow import service, models

router = APIRouter()

@router.get("/verify", response_model=Dict[str, Any])
def verify_integrity(db: Session = Depends(deps.get_db), current_user: Any = Depends(deps.get_current_user)):
    """Verify the entire SHADOW evidence chain for tampering."""
    return service.verify_chain(db)

@router.get("/replay/{entity_type}/{entity_id}", response_model=Dict[str, Any])
def replay_entity_history(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user)
):
    """Replay the life cycle of any entity from immutable logs."""
    return service.replay_state(db, entity_type, entity_id)

@router.get("/evidence/{trace_id}", response_model=Any)
def get_evidence(trace_id: str, db: Session = Depends(deps.get_db), current_user: Any = Depends(deps.get_current_user)):
    ev = service.fetch_evidence(db, trace_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return ev
