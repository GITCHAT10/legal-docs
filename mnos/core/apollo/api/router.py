from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from mnos.core.api import deps
from mnos.core.apollo.components.guard import apollo_guard
from mnos.core.apollo.components import core, monitoring, intelligence

router = APIRouter()

release_manager = core.ReleaseManager()
sync_engine = core.SyncEngine()

@router.post("/deploy/init")
async def init_apollo_deploy(
    handshake_id: str,
    channel: str = "PILOT",
    db: Session = Depends(deps.get_db),
    x_device_id: str = Header(...)
):
    """DEPLOY_INIT: Handshake for Sovereign Canary Deployment."""
    ctx = {"trace_id": f"DEPLOY-{handshake_id}", "device_id": x_device_id}

    def _execute(db: Session):
        return release_manager.init_deploy(handshake_id, channel)

    return apollo_guard.run_safe("apollo.deploy.init", ctx, _execute, db=db)

@router.post("/sync/lock")
async def lock_edge_sync(
    trace_id: str,
    db: Session = Depends(deps.get_db),
    x_device_id: str = Header(...)
):
    """SYNC_LOCK: Cryptographic seal for Edge Node data."""
    ctx = {"trace_id": trace_id, "device_id": x_device_id}
    return apollo_guard.run_safe("apollo.sync.lock", ctx, lambda db: sync_engine.sync_lock(trace_id), db=db)

@router.get("/health/status")
def get_node_health(target_id: str):
    """NODE_HEALTH_ALERT: Continuous monitor hook."""
    return {"id": target_id, "status": monitoring.health_monitor.get_status(target_id)}
