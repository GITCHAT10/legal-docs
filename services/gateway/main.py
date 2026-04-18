from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import Response
import httpx
import os
import sys
import uvicorn
from typing import Optional

app = FastAPI(title="BUILDX Gateway")

def get_services():
    return {
        "eleone": os.getenv("ELEONE_URL", "http://eleone:8001"),
        "shadow": os.getenv("SHADOW_URL", "http://shadow:8002"),
        "svd": os.getenv("SVD_URL", "http://svd:8003"),
        "sal": os.getenv("SAL_URL", "http://sal:8004"),
        "bfi": os.getenv("BFI_URL", "http://bfi:8005"),
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.api_route("/api/v1/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_proxy(service_name: str, path: str, request: Request, x_idempotency_key: Optional[str] = Header(None)):
    services = get_services()
    if service_name not in services:
        raise HTTPException(status_code=404, detail="Service not found")

    url = f"{services[service_name]}/{path}"

    async with httpx.AsyncClient() as client:
        method = request.method
        content = await request.body()
        headers = dict(request.headers)
        headers.pop("host", None)

        if x_idempotency_key:
            headers["X-Idempotency-Key"] = x_idempotency_key

        try:
            resp = await client.request(
                method,
                url,
                content=content,
                headers=headers,
                params=request.query_params,
                timeout=10.0
            )
            return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Service unavailable: {exc}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    uvicorn.run(app, host="0.0.0.0", port=port)
