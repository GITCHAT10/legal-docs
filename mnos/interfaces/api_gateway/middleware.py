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
        raise HTTPException(status_code=401, detail=f"Missing security headers: sign={signature}, ts={timestamp}, req={request_id}")

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
    # Canonical body hash - ensure we match the SDK
    if body:
        # Load and dump to ensure same format
        try:
            body_dict = json.loads(body)
            normalized_body = json.dumps(body_dict, sort_keys=True, separators=(",", ":")).encode()
            body_hash = hashlib.sha256(normalized_body).hexdigest()
        except:
            body_hash = hashlib.sha256(body).hexdigest()
    else:
        body_hash = hashlib.sha256(b"").hexdigest()

    canonical_string = f"{method}\n{path}\n{timestamp}\n{request_id}\n{body_hash}"
    expected_sig = hmac.new(
        secret.encode(),
        canonical_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if signature != expected_sig:
        raise HTTPException(status_code=401, detail="Invalid signature")

    async def receive():
        return {"type": "http.request", "body": body}

    request._receive = receive

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
