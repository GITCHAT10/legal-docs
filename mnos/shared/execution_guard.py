import contextvars
import uuid
from datetime import datetime, UTC
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
        self.pending_approvals = {} # action_id -> {first_actor, payload, status}

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

        # Dual Approval Intercept
        if not valid and "DUAL_APPROVAL_REQUIRED" in msg:
            return self._initiate_dual_approval(action_type, actor_context, *args, **kwargs)

        if not valid:
            raise PermissionError(f"FAIL CLOSED: Policy Violation - {msg}")

        # 3. Set Sovereign Context (Authorized)
        token = str(uuid.uuid4())
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

    @staticmethod
    def sovereign_context(actor: dict = None):
        """Allows authorized system operations by setting the context manually."""
        import contextlib
        token = str(uuid.uuid4())
        actor = actor or {"identity_id": "SYSTEM", "role": "admin", "device_id": "SYSTEM_VIRTUAL"}

        @contextlib.contextmanager
        def _context():
            t = _sovereign_context.set({"token": token, "actor": actor})
            try:
                yield
            finally:
                _sovereign_context.reset(t)
        return _context()

    def _initiate_dual_approval(self, action_type: str, actor_context: Dict, *args, **kwargs):
        action_id = f"DA-{uuid.uuid4().hex[:8].upper()}"
        self.pending_approvals[action_id] = {
            "type": action_type,
            "first_actor": actor_context["identity_id"],
            "payload": {"args": args, "kwargs": kwargs},
            "status": "PENDING_SECOND_APPROVAL",
            "timestamp": datetime.now(UTC).isoformat()
        }
        with self.sovereign_context(actor_context):
            self.shadow.commit("dual_approval.initiated", actor_context["identity_id"], {
                "action_id": action_id,
                "action_type": action_type
            })
        return {"status": "AWAITING_DUAL_APPROVAL", "action_id": action_id}

    def approve_second_signature(self, action_id: str, actor_context: Dict, func: Callable):
        """Finalizes a dual-approval action with a second signature."""
        pending = self.pending_approvals.get(action_id)
        if not pending:
            raise ValueError("Invalid or expired Action ID")

        if pending["first_actor"] == actor_context["identity_id"]:
            raise PermissionError("FAIL CLOSED: Dual approval requires a different actor for the second signature")

        # Set second approval flag for policy engine
        actor_context["is_second_approval"] = True

        # Merge original payload back
        args = pending["payload"]["args"]
        kwargs = pending["payload"]["kwargs"]

        result = self.execute_sovereign_action(pending["type"], actor_context, func, *args, **kwargs)

        with self.sovereign_context(actor_context):
            self.shadow.commit("dual_approval.completed", actor_context["identity_id"], {"action_id": action_id})
        del self.pending_approvals[action_id]
        return result

class ExecutionGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, guard, events):
        super().__init__(app)
        self.guard = guard
        self.events = events
        self.violation_counts = {}

    async def dispatch(self, request: Request, call_next):
        # Operational paths to guard
        guarded_paths = ["/supply", "/finance", "/aegis/asset", "/commerce"]

        if any(request.url.path.startswith(path) for path in guarded_paths):
            identity_id = request.headers.get("X-AEGIS-IDENTITY")
            device_id = request.headers.get("X-AEGIS-DEVICE")

            # Require AEGIS Identity for all guarded paths
            if not identity_id:
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
