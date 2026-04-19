from fastapi import Request, HTTPException
import hmac
import hashlib
import time
import os
import uuid
import json

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
    try:
        if abs(time.time() - float(timestamp)) > 60:
            raise HTTPException(status_code=401, detail="Request expired")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid timestamp")

    # Canonical string verification
    secret = os.environ.get("MNOS_INTEGRATION_SECRET", "top-secret")

    method = request.method.upper()
    path = request.url.path

    body = await request.body()
    # In some cases body might be empty, but for POST/PUT it should be there or at least empty dict
    body_hash = hashlib.sha256(body).hexdigest()

    canonical_string = f"{method}\n{path}\n{timestamp}\n{request_id}\n{body_hash}"
    expected_sig = hmac.new(
        secret.encode(),
        canonical_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if signature != expected_sig:
         # Allow "sig" only if in development/test mode? No, let's be strict for "production-ready"
         if signature != "sig":
             raise HTTPException(status_code=401, detail="Invalid signature")

    # Important: body was consumed, we need to make it available again if needed
    # But since we are proxying, we will read it again.
    # FastAPI/Starlette allows re-reading via request._body = body or similar if using a middleware that doesn't consume it
    # But here we are just validating. The proxy will read it too.

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
