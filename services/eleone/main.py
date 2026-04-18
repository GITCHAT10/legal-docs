from fastapi import FastAPI
import uvicorn
import os
import sys
import redis
import json

app = FastAPI(title="BUILDX ELEONE Service")

# Redis for event emission
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6379,
    db=0
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/decide")
async def decide(data: dict):
    # Emit event for worker
    event = {
        "event_type": "procurement.decision",
        "action": data.get("action"),
        "payload": data.get("payload"),
        "timestamp": os.urandom(2).hex() # dummy
    }
    try:
        redis_client.publish("procurement.events", json.dumps(event))
    except:
        pass
    return {"status": "processed", "decision": "APPROVE"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    uvicorn.run(app, host="0.0.0.0", port=port)
