from fastapi import FastAPI, Request, HTTPException, Header
import uvicorn
import os
import sys
import hashlib
import hmac
import time
import json
import redis
from typing import Dict, List, Optional

app = FastAPI(title="BUILDX Edge Node Scaffold")

# Configuration
GATEWAY_SECRET = os.getenv("GATEWAY_SECRET", "mnos-production-secret")
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=redis_host, port=6379, db=0)

decision_cache: Dict[str, dict] = {}
offline_buffer: List[dict] = []

@app.get("/health")
def health():
    return {"status": "ok"}

def verify_signature(method, path, timestamp, idempotency_key, body, signature):
    body_hash = hashlib.sha256(body).hexdigest()
    canonical_string = f"{method}|{path}|{timestamp}|{idempotency_key}|{body_hash}"
    expected = hmac.new(GATEWAY_SECRET.encode(), canonical_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.post("/execute")
async def execute(
    request: Request,
    x_idempotency_key: str = Header(...),
    x_signature: str = Header(...),
    x_timestamp: str = Header(...)
):
    body = await request.body()
    if not verify_signature(request.method, request.url.path, x_timestamp, x_idempotency_key, body, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = json.loads(body)
    action_type = data.get("action") # APPROVE / DENY / HOLD
    payload = data.get("payload", {})

    # Execute Hardware Logic
    result = execute_action(action_type, payload)

    # Audit Event
    audit_event = {
        "event": "edge_execution",
        "action": action_type,
        "idempotency_key": x_idempotency_key,
        "result": result,
        "timestamp": time.time()
    }

    try:
        redis_client.publish("audit.events", json.dumps(audit_event))
    except:
        offline_buffer.append(audit_event)

    decision_cache[x_idempotency_key] = audit_event
    return {"status": "executed", "result": result}

def execute_action(action_type: str, payload: dict):
    print(f"⚙️ [HARDWARE] Executing {action_type} with payload: {payload}")
    if action_type in ["APPROVE", "DENY", "HOLD"]:
        return {"code": "SUCCESS", "message": f"Action {action_type} applied"}
    return {"code": "ERROR", "message": f"Unknown action: {action_type}"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8006))
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    uvicorn.run(app, host="0.0.0.0", port=port)
