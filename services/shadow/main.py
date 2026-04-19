from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import hashlib
import json
import os
import sys
import uvicorn
import time
import redis

app = FastAPI(title="BUILDX SHADOW Immutable Ledger")

# Redis for audit notifications
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=redis_host, port=6379, db=0)

ledger = []

@app.get("/health")
def health():
    return {"status": "ok", "service": "shadow"}

@app.post("/entry")
async def add_entry(data: dict):
    prev_hash = ledger[-1]["current_hash"] if ledger else "0"*64
    content = json.dumps(data, sort_keys=True) + prev_hash
    curr_hash = hashlib.sha256(content.encode()).hexdigest()

    entry = {
        "index": len(ledger),
        "data": data,
        "previous_hash": prev_hash,
        "current_hash": curr_hash,
        "timestamp": time.time()
    }
    ledger.append(entry)

    try:
        redis_client.publish("audit.events", json.dumps({"event": "ledger_append", "hash": curr_hash}))
    except:
        pass

    return entry

@app.get("/verify-integrity")
async def verify():
    errors = []
    for i in range(len(ledger)):
        expected_prev = ledger[i-1]["current_hash"] if i > 0 else "0"*64
        if ledger[i]["previous_hash"] != expected_prev:
            errors.append(f"Mismatch at {i}")
    return {"status": "valid" if not errors else "corrupted", "errors": errors}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
