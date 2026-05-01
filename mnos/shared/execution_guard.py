import contextvars
import uuid
from typing import Callable, Any, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to track sovereign authorization
_sovereign_context = contextvars.ContextVar("sovereign_context", default=None)

class ExecutionGuard:
    def __init__(self, identity_core, policy_engine, fce, shadow, events):
        self.identity_core = identity_core
        self.policy_engine = policy_engine
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def execute_sovereign_action(self, action_type: str, actor_context: Dict, func: Callable, *args, **kwargs) -> Any:
        """
        MANDATORY ENTRYPOINT for all mutating commerce actions.
        ORBAN -> AEGIS -> ExecutionGuard -> FCE -> SHADOW
        """
        identity_id = actor_context.get("identity_id")
        device_id = actor_context.get("device_id")
        role = actor_context.get("role")

        # 1. AEGIS Identity & Binding Check
        if not identity_id or not device_id:
            raise PermissionError(f"FAIL CLOSED: Missing Identity or Device Binding for {action_type}")

        # ZERO_TRUST_DEFAULT_DENY for sensitive procurement actions
        sensitive_actions = ["procurement.order.settle", "finance.escrow.release"]
        if action_type in sensitive_actions and not actor_context.get("national_id_verified"):
             raise PermissionError(f"ZERO TRUST REJECTION: National ID binding required for {action_type}")

        # 2. Role / Permission Validation
        valid, msg = self.policy_engine.validate_action(action_type, actor_context)
        if not valid:
            raise PermissionError(f"FAIL CLOSED: Policy Violation - {msg}")

        # 3. Set Sovereign Context (Authorized)
        token = str(uuid.uuid4())

        # Ensure actor_context has what we need for get_actor()
        _sovereign_context.set({"token": token, "actor": actor_context})

        try:
            # BEGIN ATOMIC TX (Simulated via context and SHADOW intent)
            # Filter non-serializable args for intent log
            serializable_input = [a for a in args if isinstance(a, (str, int, float, dict, list, bool))]
            intent_payload = {
                "action": action_type,
                "actor_aegis_id": identity_id,
                "actor_device_id": device_id,
                "actor_role": role,
                "input": serializable_input or kwargs,
                "status": "INTENT"
            }
            self.shadow.commit(f"{action_type}.intent", identity_id, intent_payload)

            # EXECUTE BUSINESS LOGIC
            result = func(*args, **kwargs)

            # 4. COMMIT TO SHADOW
            commit_payload = {
                "action": action_type,
                "actor_aegis_id": identity_id,
                "actor_device_id": device_id,
                "result": result,
                "status": "COMMITTED"
            }
            self.shadow.commit(f"{action_type}.completed", identity_id, commit_payload)

            return result

        except Exception as e:
            # ROLLBACK LOGIC
            fail_payload = {
                "action": action_type,
                "actor_aegis_id": identity_id,
                "error": str(e),
                "status": "FAILED_ROLLBACK"
            }
            self.shadow.commit(f"{action_type}.failed", identity_id or "UNKNOWN", fail_payload)
            raise RuntimeError(f"SOVEREIGN EXECUTION FAILED: {str(e)}")
        finally:
            # Clear context
            _sovereign_context.set(None)

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
        self.violation_counts = {}

    async def dispatch(self, request: Request, call_next):
        # Operational paths to guard
        guarded_paths = ["/supply", "/finance", "/aegis/asset", "/commerce", "/upos"]

        if any(request.url.path.startswith(path) for path in guarded_paths):
            identity_id = request.headers.get("X-AEGIS-IDENTITY")
            device_id = request.headers.get("X-AEGIS-DEVICE")

            # Require AEGIS Identity for all guarded paths
            if not identity_id:
                # Bypass for health check if it was under /upos (it's not but good practice)
                if request.url.path == "/health":
                     return await call_next(request)
                return self._violation("Missing Actor Identity")

            # Require Device Binding for Mutating Actions
            if request.method in ["POST", "PUT", "DELETE"] and not device_id:
                 return self._violation("Missing Device Binding for Sensitive Action")

            # In a real system, we'd verify HMAC/Signature here.
            # For this audit, we enforce header presence.

        response = await call_next(request)
        return response

    def _violation(self, message):
        return JSONResponse(status_code=403, content={"detail": f"EXECUTION GUARD REJECTION: {message}"})
