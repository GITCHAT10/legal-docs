import logging
from typing import Callable, Any, Dict
from fastapi import HTTPException
from mnos.modules.shadow import service as shadow_service

class APOLLOExecutionGuard:
    """
    Sovereign Execution Guard for APOLLO Control Plane.
    Mode: SOVEREIGN-HARDENED
    Enforce: AEGIS_DEVICE_BINDING, SERVER_SIDE_VALIDATION
    Audit: SHADOW_CHAIN_STRICT
    Fail-Mode: FAIL-CLOSED
    """

    def run_safe(self, action: str, ctx: Dict[str, Any], func: Callable, *args, **kwargs) -> Any:
        db = kwargs.get("db") or (args[0] if args else None)
        trace_id = ctx.get("trace_id")

        if not trace_id:
            raise HTTPException(status_code=400, detail="APOLLO Guard: Trace ID Required")

        # 1. AEGIS Device Binding check
        if not ctx.get("device_id"):
            logging.error(f"APOLLO FAIL-CLOSED: Device Binding Missing for {trace_id}")
            raise HTTPException(status_code=401, detail="Sovereign Failure: Device Not Bound")

        # 2. Strict SHADOW intent
        shadow_service.commit_evidence(db, trace_id, {
            "system": "APOLLO-CONTROL-PLANE",
            "action": action,
            "stage": "SOVEREIGN_INTENT",
            "context": ctx
        })

        try:
            result = func(*args, **kwargs)

            # 3. Final SHADOW lock
            shadow_service.commit_evidence(db, trace_id, {
                "action": action,
                "stage": "SOVEREIGN_COMMIT",
                "status": "HARDENED"
            })
            return result
        except Exception as e:
            logging.error(f"APOLLO Sovereign Failure: {e}")
            if db: db.rollback()
            raise HTTPException(status_code=500, detail="APOLLO FAIL-CLOSED: System Blocked")

apollo_guard = APOLLOExecutionGuard()
