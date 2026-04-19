from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import sys
import redis
import json
import time

app = FastAPI(title="BUILDX ELEONE Decision Engine")

# Redis for event emission
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=redis_host, port=6379, db=0)

class DecisionRequest(BaseModel):
    action: str
    payload: dict

@app.get("/health")
def health():
    return {"status": "ok", "service": "eleone"}

@app.post("/decide")
async def decide(request: DecisionRequest):
    # Real-time decision logic
    decision = "APPROVE"
    if request.payload.get("amount", 0) > 1000000:
        decision = "HOLD"

    event = {
        "event_type": "procurement.decision",
        "action": request.action,
        "payload": request.payload,
        "decision": decision,
        "timestamp": time.time()
    }

    try:
        redis_client.publish("procurement.events", json.dumps(event))
    except Exception as e:
        print(f"Redis Publish Error: {e}")

    return {"status": "processed", "decision": decision}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
