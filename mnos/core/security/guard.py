import logging
from typing import Callable, Any, Dict
from fastapi import HTTPException
from mnos.modules.shadow import service as shadow_service
import asyncio

class ExecutionGuard:
    """
    MNOS Execution Guard.
    Ensures every sovereign action passes through the required security and audit gates.
    Law: ORBAN -> AEGIS -> ExecutionGuard -> FCE -> SHADOW
    """

    def _begin_action(self, db, action_name: str, ctx: Dict[str, Any]):
        trace_id = ctx.get("trace_id")
        if not trace_id:
            raise HTTPException(status_code=400, detail="ExecutionGuard: Missing mandatory trace_id")

        logging.info(f"ExecutionGuard: BEGIN {action_name} [{trace_id}]")

        # Identity check
        if not ctx.get("aegis_id"):
            raise HTTPException(status_code=401, detail="ExecutionGuard: AEGIS identity missing")

        # Log Intent to SHADOW
        shadow_service.commit_evidence(db, trace_id, {
            "action": action_name,
            "stage": "INTENT",
            "actor": ctx.get("aegis_id"),
            "context": ctx
        })

    def _commit_action(self, db, action_name: str, ctx: Dict[str, Any]):
        trace_id = ctx.get("trace_id")
        shadow_service.commit_evidence(db, trace_id, {
            "action": action_name,
            "stage": "SUCCESS",
            "actor": ctx.get("aegis_id"),
            "result": "COMMITTED"
        })
        logging.info(f"ExecutionGuard: COMMIT {action_name} [{trace_id}]")

    def _fail_action(self, db, action_name: str, ctx: Dict[str, Any], e: Exception):
        trace_id = ctx.get("trace_id")
        logging.error(f"ExecutionGuard: FAIL {action_name} [{trace_id}]: {e}")
        if db:
            db.rollback()

        # Log Failure to SHADOW
        try:
            shadow_service.commit_evidence(db, trace_id, {
                "action": action_name,
                "stage": "FAILURE",
                "reason": str(e)
            })
        except:
            pass

        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Sovereign Execution Error: {action_name} failed")

    def execute_sovereign_action(
        self,
        action_name: str,
        ctx: Dict[str, Any],
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        db = kwargs.get("db") or (args[0] if args else None)
        self._begin_action(db, action_name, ctx)
        try:
            result = func(*args, **kwargs)
            self._commit_action(db, action_name, ctx)
            return result
        except Exception as e:
            self._fail_action(db, action_name, ctx, e)

    async def execute_sovereign_action_async(
        self,
        action_name: str,
        ctx: Dict[str, Any],
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        db = kwargs.get("db") or (args[0] if args else None)
        self._begin_action(db, action_name, ctx)
        try:
            result = await func(*args, **kwargs)
            self._commit_action(db, action_name, ctx)
            return result
        except Exception as e:
            self._fail_action(db, action_name, ctx, e)

guard = ExecutionGuard()
