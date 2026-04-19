from fastapi import FastAPI, HTTPException
import httpx
import os
import uvicorn
import uuid

app = FastAPI(title="MNOS Module Router")

ELEONE_URL = "http://eleone:8001"
SHADOW_URL = "http://shadow:8002"

MODULE_URLS = {
    "xport": "http://xport:8000",
    "aqua": "http://aqua:8000",
    "inn": "http://inn:8000",
    "skygodown": "http://skygodown:8000",
    "atollairways": "http://atollairways:8000",
}

@app.get("/health")
def health():
    return {"status": "ok", "service": "mnos_router"}

@app.post("/route")
async def route_module_flow(request: dict):
    module_name = request.get("module")
    if module_name not in MODULE_URLS:
        raise HTTPException(status_code=400, detail=f"Unknown module: {module_name}")

    event_id = str(uuid.uuid4())

    async with httpx.AsyncClient() as client:
        # 1. CORE Decision
        decision_resp = await client.post(f"{ELEONE_URL}/decide", json=request)
        decision_data = decision_resp.json()
        decision = decision_data["decision"]

        # 2. Module Execution (if approved)
        result = "SKIPPED"
        if decision == "APPROVE":
            exec_resp = await client.post(f"{MODULE_URLS[module_name]}/execute", json=request)
            result = exec_resp.json().get("status", "SUCCESS")

        # 3. SHADOW Commitment
        shadow_payload = {
            "event_id": event_id,
            "decision": decision,
            "result": result,
            "data": request
        }
        shadow_resp = await client.post(f"{SHADOW_URL}/commit", json=shadow_payload)
        shadow_data = shadow_resp.json()

        # 4. Final Enveloped Response
        return {
            "shadow_id": shadow_data["shadow_id"],
            "event_id": event_id,
            "decision": decision,
            "result": result,
            "audit_hash": shadow_data["audit_hash"]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
