from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import Response
import httpx
import os
import sys
import uvicorn
import hashlib
import hmac
import time
import json
import uuid
import redis
from typing import Optional

app = FastAPI(title="BUILDX Hardened Gateway")

# Shared secret for signature verification
SECRET_KEY = os.getenv("GATEWAY_SECRET", "mnos-production-secret")

# Redis for event emission and replay protection
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

def get_services():
    return {
        "eleone": os.getenv("ELEONE_URL", "http://localhost:8001"),
        "shadow": os.getenv("SHADOW_URL", "http://localhost:8002"),
        "svd": os.getenv("SVD_URL", "http://localhost:8003"),
        "sal": os.getenv("SAL_URL", "http://localhost:8004"),
        "bfi": os.getenv("BFI_URL", "http://localhost:8005"),
        "edge": os.getenv("EDGE_URL", "http://localhost:8006"),
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}

@app.get("/system/status")
async def system_status():
    status = {}
    services = get_services()
    async with httpx.AsyncClient() as client:
        for name, url in services.items():
            try:
                resp = await client.get(f"{url}/health", timeout=1.0)
                status[name] = "healthy" if resp.status_code == 200 else "unhealthy"
            except:
                status[name] = "down"

    try:
        redis_client.ping()
        status["redis"] = "connected"
    except:
        status["redis"] = "disconnected"

    return status

@app.api_route("/api/v1/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_proxy(
    service_name: str,
    path: str,
    request: Request,
    x_idempotency_key: str = Header(...),
    x_signature: str = Header(...),
    x_timestamp: str = Header(...)
):
    # 1. Verify Timestamp (Anti-replay window)
    try:
        ts = float(x_timestamp)
        if abs(time.time() - ts) > 300:
            raise HTTPException(status_code=401, detail="Request timestamp expired")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp")

    # 2. Replay Protection (Idempotency Key Cache)
    try:
        if redis_client.exists(f"idempotency:{x_idempotency_key}"):
            raise HTTPException(status_code=409, detail="Duplicate request")
        redis_client.setex(f"idempotency:{x_idempotency_key}", 3600, "1")
    except:
        pass

    # 3. Verify Signature
    body = await request.body()
    body_hash = hashlib.sha256(body).hexdigest()
    canonical_string = f"{request.method}|{request.url.path}|{x_timestamp}|{x_idempotency_key}|{body_hash}"
    expected_signature = hmac.new(SECRET_KEY.encode(), canonical_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 4. Route to Service
    services = get_services()
    if service_name not in services:
        raise HTTPException(status_code=404, detail="Service not found")

    url = f"{services[service_name]}/{path}"
    request_id = str(uuid.uuid4())

    # 5. Emit Event
    event_payload = {
        "event": "request_proxied",
        "request_id": request_id,
        "service": service_name,
        "path": path,
        "method": request.method,
        "timestamp": time.time()
    }
    try:
        redis_client.publish("audit.events", json.dumps(event_payload))
    except:
        pass

    async with httpx.AsyncClient() as client:
        headers = dict(request.headers)
        headers.pop("host", None)
        headers["X-Request-ID"] = request_id

        try:
            resp = await client.request(
                request.method,
                url,
                content=body,
                headers=headers,
                params=request.query_params,
                timeout=10.0
            )
            return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Service unavailable: {exc}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
