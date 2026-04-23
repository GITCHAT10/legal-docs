from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class ExecutionGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, identity_core, policy_engine, events):
        super().__init__(app)
        self.identity_core = identity_core
        self.policy_engine = policy_engine
        self.events = events
        self.violation_counts = {}

    async def dispatch(self, request: Request, call_next):
        # Operational paths to guard
        guarded_paths = ["/supply", "/finance", "/aegis/asset"]

        if any(request.url.path.startswith(path) for path in guarded_paths):
            identity_id = request.headers.get("X-AEGIS-IDENTITY")
            device_id = request.headers.get("X-AEGIS-DEVICE")

            if not identity_id:
                return await self._handle_violation(request, "Missing Actor Identity")

            # Basic sensitive action check
            if request.method in ["POST", "PUT", "DELETE"] and not device_id:
                 return await self._handle_violation(request, "Missing Device Binding for Sensitive Action")

            # Policy check
            action_type = self._map_path_to_action(request.url.path)
            valid, msg = self.policy_engine.validate_action(action_type, {
                "identity_id": identity_id,
                "device_id": device_id
            })

            if not valid:
                return await self._handle_violation(request, msg)

        response = await call_next(request)
        return response

    async def _handle_violation(self, request, message):
        identity_id = request.headers.get("X-AEGIS-IDENTITY", "anonymous")
        self.violation_counts[identity_id] = self.violation_counts.get(identity_id, 0) + 1

        if self.violation_counts[identity_id] > 5:
            self.events.publish("SECURITY_ALERT", {
                "identity_id": identity_id,
                "reason": "Repeated Violations",
                "target": "MIG_SECURITY_COMMAND"
            })

        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403, content={"detail": f"EXECUTION GUARD REJECTION: {message}"})

    def _map_path_to_action(self, path):
        if "payout" in path: return "payout"
        if "delivery" in path: return "delivery_acceptance"
        if "asset" in path: return "asset_assignment"
        return "generic_operational_action"
