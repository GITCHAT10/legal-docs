from fastapi import FastAPI, Request, HTTPException, Header
import httpx
import os
import uvicorn
import uuid
import time
import hashlib
import hmac
import json

app = FastAPI(title="MNOS API Bridge Layer")

# Shared secret for signature validation
SECRET_KEY = os.getenv("MNOS_GATEWAY_SECRET", "mnos-prod-secret")

ROUTER_URL = os.getenv("ROUTER_URL", "http://localhost:8003")
ELEONE_URL = os.getenv("ELEONE_URL", "http://localhost:8001")
SHADOW_URL = os.getenv("SHADOW_URL", "http://localhost:8002")

@app.get("/health")
def health():
    return {"status": "ok", "service": "mnos_api"}

async def validate_mnos_request(request: Request, x_signature: str, x_timestamp: str, x_idempotency_key: str):
    try:
        if abs(time.time() - float(x_timestamp)) > 300:
            raise HTTPException(status_code=401, detail="Request expired")
    except:
        raise HTTPException(status_code=400, detail="Invalid timestamp")

    body = await request.body()
    canonical = f"{request.method}|{request.url.path}|{x_timestamp}|{x_idempotency_key}|{hashlib.sha256(body).hexdigest()}"
    expected = hmac.new(SECRET_KEY.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_signature):
        raise HTTPException(status_code=401, detail="Invalid MNOS signature")

@app.post("/mnos/v1/event")
async def handle_event(
    request: Request,
    x_signature: str = Header(...),
    x_timestamp: str = Header(...),
    x_idempotency_key: str = Header(...)
):
    await validate_mnos_request(request, x_signature, x_timestamp, x_idempotency_key)
    body = await request.json()

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{ROUTER_URL}/route", json=body)
        return resp.json()

@app.post("/mnos/v1/decision")
async def handle_decision(
    request: Request,
    x_signature: str = Header(...),
    x_timestamp: str = Header(...),
    x_idempotency_key: str = Header(...)
):
    await validate_mnos_request(request, x_signature, x_timestamp, x_idempotency_key)
    body = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{ELEONE_URL}/decide", json=body)
        return resp.json()

@app.get("/mnos/v1/audit/{id}")
async def handle_audit(id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{SHADOW_URL}/audit/{id}")
        return resp.json()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
