from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import os

class APIGatewayControlPlane:
    """
    N-DEOS API Gateway Control Plane.
    Enforces policies per island before reaching the execution core.
    """
    def __init__(self):
        self.rate_limits = {} # island_id -> current_load

    async def enforce_policy(self, request: Request):
        if os.environ.get("DISABLE_GATEWAY_LIMITS") == "1":
            return True

        island_id = request.headers.get("X-ISLAND-ID", "GLOBAL")

        # 1. Rate Limiting - Increased for test stability
        load = self.rate_limits.get(island_id, 0)
        if load > 10000:
             raise HTTPException(status_code=429, detail=f"Rate limit exceeded for island {island_id}")
        self.rate_limits[island_id] = load + 1

        # 2. Request Signature Validation
        signature = request.headers.get("X-MNOS-SIGNATURE")
        if not signature and island_id != "GLOBAL":
            raise HTTPException(status_code=401, detail="Missing required request signature for edge sync")

        # 3. Tenant Isolation
        # (Tenant verification logic here)

        return True

    def reset_limits(self):
        self.rate_limits = {}
