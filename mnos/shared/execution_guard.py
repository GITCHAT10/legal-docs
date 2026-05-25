import uuid
from typing import Callable, Any, Dict, Optional, List
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import contextmanager
from mnos.shared.auth_context import set_sovereign_context, reset_sovereign_context, is_sovereign_authorized, get_sovereign_actor

STRICT_GUARD_PATHS = [
    "/supply", "/finance", "/aegis/asset", "/commerce",
    "/imoxon/orders", "/imoxon/products", "/imoxon/suppliers", "/upos",
    "/prestige/supplier-portal"
]

DUAL_AUTH_PATHS = ["/bubble", "/exmail", "/iluvia/app", "/orca", "/pms", "/csr"]

class ExecutionGuard:
    def __init__(self, identity_core, policy_engine, fce, shadow, events):
        self.identity_core = identity_core
        self.policy_engine = policy_engine
        self.fce = fce
        self.shadow = shadow
        self.events = events

    @contextmanager
    def sovereign_context(self, actor_context: Dict):
        token = set_sovereign_context(actor_context)
        try:
            yield
        finally:
            reset_sovereign_context(token)

    def execute_sovereign_action(self, action_type: str, actor_context: Dict, func: Callable, *args, **kwargs) -> Any:
        identity_id = actor_context.get("identity_id")
        device_id = actor_context.get("device_id")
        role = actor_context.get("role")

        if actor_context.get("realm") != "SYSTEM":
            if not identity_id:
                raise PermissionError("FAIL CLOSED: Missing Identity")
            is_sensitive = any(s in action_type.lower() for s in ["imoxon", "procurement", "fce", "supply", "prestige"])
            if not device_id and is_sensitive:
                raise PermissionError("FAIL CLOSED: Missing Device Binding")

        if actor_context.get("realm") != "SYSTEM":
            valid, msg = self.policy_engine.validate_action(action_type, actor_context)
            if not valid:
                raise PermissionError(f"FAIL CLOSED: Policy Violation - {msg}")

        with self.sovereign_context(actor_context):
            try:
                trace_id = actor_context.get("trace_id") or str(uuid.uuid4().hex[:8])
                self.shadow.commit(f"{action_type}.intent", identity_id or "SYSTEM", {"trace_id": trace_id})
                result = func(*args, **kwargs)
                self.shadow.commit(f"{action_type}.completed", identity_id or "SYSTEM", {"trace_id": trace_id, "result": result})
                return result
            except Exception as e:
                try:
                    self.shadow.commit(f"{action_type}.failed", identity_id or "UNKNOWN", {"error": str(e)})
                except:
                    pass
                from mnos.shared.exceptions import ExecutionValidationError
                if isinstance(e, (ExecutionValidationError, PermissionError)):
                    raise e
                raise RuntimeError(f"SOVEREIGN EXECUTION FAILED: {str(e)}")

    @staticmethod
    def is_authorized() -> bool:
        return is_sovereign_authorized()

    @staticmethod
    def get_actor() -> Optional[Dict]:
        return get_sovereign_actor()

class ExecutionGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, guard, events):
        super().__init__(app)
        self.guard = guard
        self.events = events

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Starlette headers are case-insensitive.
        identity_id = request.headers.get("x-aegis-identity")
        device_id = request.headers.get("x-aegis-device")
        session_id = request.headers.get("x-aegis-session")

        require_strict = any(path.startswith(p) for p in STRICT_GUARD_PATHS)
        allow_dual = any(path.startswith(p) for p in DUAL_AUTH_PATHS)

        if require_strict:
            if not (identity_id and device_id):
                return self._violation("Strict endpoint requires identity and device", 403)

        if allow_dual:
            if not ((identity_id and device_id) or session_id):
                return self._violation("Authentication required", 401)

        return await call_next(request)

    def _violation(self, message, code):
        return JSONResponse(status_code=code, content={"detail": message})
