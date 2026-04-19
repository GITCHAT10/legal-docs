from fastapi import Request, HTTPException
import hmac
import hashlib
import time
import os

async def signature_validation_middleware(request: Request, call_next):
    # Skip for health check
    if request.url.path == "/health":
        return await call_next(request)

    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")
    request_id = request.headers.get("X-Request-Id")

    if not all([signature, timestamp, request_id]):
        raise HTTPException(status_code=401, detail="Missing security headers")

    # Time window validation (60 seconds)
    if abs(time.time() - float(timestamp)) > 60:
        raise HTTPException(status_code=401, detail="Request expired")

    # In a real implementation, verify HMAC-SHA256 signature
    # secret = os.environ.get("MNOS_INTEGRATION_SECRET")

    return await call_next(request)

async def idempotency_middleware(request: Request, call_next):
    if request.method in ["POST", "PUT"]:
        idempotency_key = request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            raise HTTPException(status_code=400, detail="Missing idempotency key")
    return await call_next(request)

async def audit_correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id
    return response

import uuid
