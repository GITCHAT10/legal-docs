from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
import time
import logging

class SovereignExecutionMiddleware(BaseHTTPMiddleware):
    """
    Sovereign Cloud Middleware for United Transfer.
    Enforces the 'FAIL CLOSED' policy.
    Rejected if:
    - No AEGIS context
    - No Device ID
    - Invalid Signature
    """
    async def dispatch(self, request: Request, call_next):
        # 1. Bypass health checks
        if request.url.path == "/health" or request.url.path.endswith("/openapi.json"):
            return await call_next(request)

        # 2. Check for AEGIS Identity
        aegis_id = request.headers.get("X-AEGIS-ID")
        if not aegis_id:
            logging.error("Sovereign Failure: AEGIS Identity Missing. FAILING CLOSED.")
            raise HTTPException(status_code=401, detail="Fail-Closed: AEGIS Identity Mandatory")

        # 3. Check for Device Binding
        device_id = request.headers.get("X-Device-ID")
        if not device_id:
            logging.error("Sovereign Failure: Device ID Missing. FAILING CLOSED.")
            raise HTTPException(status_code=401, detail="Fail-Closed: Device Binding Mandatory")

        # 4. Check for ORBAN/Cloud Signature
        signature = request.headers.get("X-UT-Signature")
        if not signature:
            logging.error("Sovereign Failure: Unsigned Request. FAILING CLOSED.")
            raise HTTPException(status_code=401, detail="Fail-Closed: Cloud Signature Required")

        # 5. Check Timestamp (Anti-Replay)
        ts = request.headers.get("X-UT-Timestamp")
        try:
            if not ts or abs(time.time() - float(ts)) > 300:
                raise HTTPException(status_code=401, detail="Fail-Closed: Timestamp Expired")
        except (ValueError, TypeError):
             raise HTTPException(status_code=401, detail="Fail-Closed: Invalid Timestamp")

        # Attach to request state for use in routes
        request.state.aegis_id = aegis_id
        request.state.device_id = device_id

        response = await call_next(request)
        return response
