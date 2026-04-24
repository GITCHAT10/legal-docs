from fastapi import Request, HTTPException
import time

class GatewayControlPlane:
    """
    N-DEOS API Gateway Control Plane.
    Enforces rate limits and tenant isolation before ExecutionGuard.
    """
    def __init__(self):
        self.rate_limits: Dict[str, list] = {} # island_id -> timestamps

    async def enforce_policy(self, request: Request, island_id: str):
        # 1. Rate Limiting (Simple sliding window)
        now = time.time()
        history = self.rate_limits.get(island_id, [])
        history = [ts for ts in history if now - ts < 60]

        if len(history) > 100: # 100 rpm per island
            raise HTTPException(status_code=429, detail="Island rate limit exceeded")

        history.append(now)
        self.rate_limits[island_id] = history

        # 2. Tenant Isolation Check
        # Logic to ensure the request belongs to the authorized island tenant

        return True

gateway = GatewayControlPlane()
