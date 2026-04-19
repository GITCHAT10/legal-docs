from fastapi import FastAPI, Request, Response, HTTPException
from typing import Any, Dict
import uuid
import os
import httpx
from .middleware import signature_validation_middleware, idempotency_middleware, audit_correlation_middleware

app = FastAPI(title="MNOS API Gateway")

@app.middleware("http")
async def add_security_and_audit(request: Request, call_next):
    return await audit_correlation_middleware(request,
        lambda req: idempotency_middleware(req,
            lambda r: signature_validation_middleware(r, call_next)))

CORE_SERVICES = {
    "aegis": "http://aegis:8001",
    "shadow": "http://shadow:8002",
    "eleone": "http://eleone:8003",
    "events": "http://events:8004",
    "fce": "http://fce:8005"
}

@app.api_route("/api/core/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def core_proxy(service: str, path: str, request: Request):
    if service not in CORE_SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")

    url = f"{CORE_SERVICES[service]}/api/core/{service}/{path}"
    async with httpx.AsyncClient() as client:
        method = request.method
        content = await request.body()
        headers = dict(request.headers)
        # Remove host header to avoid conflicts
        headers.pop("host", None)

        response = await client.request(method, url, content=content, headers=headers, timeout=10.0)
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))

@app.get("/health")
async def health():
    return {"status": "ok"}
