import contextvars
import uuid
from typing import Callable, Any, Dict, Optional, List
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import contextmanager
import os

# Context variable to track sovereign authorization
_sovereign_context = contextvars.ContextVar("sovereign_context", default=None)

# Paths that require elevated guard (financial, supply, audit, commerce mutations)
STRICT_GUARD_PATHS = [
    "/supply", "/finance", "/aegis/asset", "/commerce",
    "/imoxon/orders", "/imoxon/products", "/imoxon/suppliers", "/upos"
]

# Paths that support dual auth (user-facing: chat, email, portal, dashboards)
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
        """Context manager to set and clear sovereign context."""
        token = _sovereign_context.set({"token": str(uuid.uuid4()), "actor": actor_context})
        try:
            yield
        finally:
            _sovereign_context.reset(token)

    def execute_sovereign_action(self, action_type: str, actor_context: Dict, func: Callable, *args, **kwargs) -> Any:
        """
        MANDATORY ENTRYPOINT for all mutating commerce actions.
        ORBAN -> AEGIS -> ExecutionGuard -> FCE -> SHADOW
        """
        identity_id = actor_context.get("identity_id")
        device_id = actor_context.get("device_id")
        role = actor_context.get("role")

        # 1. AEGIS Identity & Binding Check
        if actor_context.get("realm") != "SYSTEM":
            if not identity_id:
                raise PermissionError(f"FAIL CLOSED: Missing Identity for {action_type}")
            # Device binding strictly required for sensitive mutations
            # Guard by action name patterns for commerce/finance/procurement
            sensitive_actions = ["imoxon", "procurement", "fce", "supply"]
            is_strict = any(s in action_type.lower() for s in sensitive_actions)
            if not device_id and is_strict:
                raise PermissionError(f"FAIL CLOSED: Missing Device Binding for sensitive action {action_type}")

        # 2. Role / Permission Validation
        if actor_context.get("realm") != "SYSTEM":
            valid, msg = self.policy_engine.validate_action(action_type, actor_context)
            if not valid:
                raise PermissionError(f"FAIL CLOSED: Policy Violation - {msg}")

        # 3. Set Sovereign Context (Authorized)
        with self.sovereign_context(actor_context):
            try:
                # Resolve trace_id for linking Prestige → MAC_EOS
                trace_id = actor_context.get("trace_id") or str(uuid.uuid4().hex[:8])

                # BEGIN ATOMIC TX
                serializable_input = [a for a in args if isinstance(a, (str, int, float, dict, list, bool))]
                intent_payload = {
                    "trace_id": trace_id,
                    "action": action_type,
                    "actor_aegis_id": identity_id,
                    "actor_device_id": device_id,
                    "actor_role": role,
                    "input": serializable_input or kwargs,
                    "status": "INTENT"
                }
                self.shadow.commit(f"{action_type}.intent", identity_id or "SYSTEM", intent_payload)

                # EXECUTE BUSINESS LOGIC
                result = func(*args, **kwargs)

                # 4. COMMIT TO SHADOW
                commit_payload = {
                    "trace_id": trace_id,
                    "action": action_type,
                    "actor_aegis_id": identity_id,
                    "actor_device_id": device_id,
                    "result": result,
                    "status": "COMMITTED"
                }
                self.shadow.commit(f"{action_type}.completed", identity_id or "SYSTEM", commit_payload)

                return result

            except Exception as e:
                # Resolve trace_id for rollback log
                trace_id = actor_context.get("trace_id") or "UNKNOWN"

                # ROLLBACK LOGIC
                fail_payload = {
                    "trace_id": trace_id,
                    "action": action_type,
                    "actor_aegis_id": identity_id,
                    "error": str(e),
                    "status": "FAILED_ROLLBACK"
                }
                self.shadow.commit(f"{action_type}.failed", identity_id or "UNKNOWN", fail_payload)

                # If it's a validation error, re-raise it directly to trigger 400
                from mnos.shared.exceptions import ExecutionValidationError
                if isinstance(e, ExecutionValidationError):
                    raise e
                raise RuntimeError(f"SOVEREIGN EXECUTION FAILED: {str(e)}")

    @staticmethod
    def is_authorized() -> bool:
        return _sovereign_context.get() is not None

    @staticmethod
    def get_actor() -> Optional[Dict]:
        ctx = _sovereign_context.get()
        return ctx["actor"] if ctx else None

class ExecutionGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, guard, events):
        super().__init__(app)
        self.guard = guard
        self.events = events

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip for public/internal endpoints
        if path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Determine required auth level
        require_strict = any(path.startswith(p) for p in STRICT_GUARD_PATHS)
        allow_dual = any(path.startswith(p) for p in DUAL_AUTH_PATHS)

        if not (require_strict or allow_dual):
            return await call_next(request)

        session_id = request.headers.get("X-AEGIS-SESSION")
        identity_id = request.headers.get("X-AEGIS-IDENTITY")
        device_id = request.headers.get("X-AEGIS-DEVICE")

        # 1. Strict Path Enforcement (Identity + Device required)
        if require_strict:
            if not (identity_id and device_id):
                # Use sovereign context for logging infrastructure failure
                with self.guard.sovereign_context({"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}):
                    self.guard.shadow.commit("shield.strict_auth_failed", "SYSTEM", {
                        "path": path, "reason": "IDENTITY_DEVICE_REQUIRED"
                    })
                return self._violation("Strict endpoint requires X-AEGIS-IDENTITY + X-AEGIS-DEVICE", 403)

        # 2. Dual Auth Paths (Identity+Device OR Session)
        if allow_dual:
            # ALLOW: (Identity AND Device) OR Session
            if not ((identity_id and device_id) or session_id):
                with self.guard.sovereign_context({"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}):
                    self.guard.shadow.commit("shield.dual_auth_failed", "SYSTEM", {
                        "path": path, "reason": "NO_VALID_CREDENTIALS"
                    })
                return self._violation("Authentication required: provide Identity+Device headers or session token", 401)

        response = await call_next(request)
        return response

    def _violation(self, message, code):
        return JSONResponse(status_code=code, content={"detail": message})
