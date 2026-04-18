from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import hashlib
import json
import os
import redis

app = FastAPI(title="SHADOW Ledger Service")

# Redis for event notification
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0
)

# Mock in-memory ledger
ledger = []

class LedgerEntry(BaseModel):
    data: dict
    previous_hash: str = ""
    current_hash: str = ""

@app.get("/health")
async def health():
    return {"status": "ok", "service": "shadow"}

@app.post("/entry")
async def add_entry(data: dict):
    previous_hash = "0" * 64
    if ledger:
        previous_hash = ledger[-1]["current_hash"]

    entry_str = json.dumps(data, sort_keys=True) + previous_hash
    current_hash = hashlib.sha256(entry_str.encode()).hexdigest()

    entry = {
        "data": data,
        "previous_hash": previous_hash,
        "current_hash": current_hash
    }
    ledger.append(entry)

    # Notify event bus of new ledger entry
    try:
        redis_client.publish("audit.events", json.dumps({"action": "ledger_append", "hash": current_hash}))
    except:
        pass

    return entry

@app.get("/verify")
async def verify_ledger():
    for i in range(1, len(ledger)):
        prev_hash = ledger[i-1]["current_hash"]
        if ledger[i]["previous_hash"] != prev_hash:
            return {"status": "corrupted", "index": i}

        entry_str = json.dumps(ledger[i]["data"], sort_keys=True) + ledger[i]["previous_hash"]
        expected_hash = hashlib.sha256(entry_str.encode()).hexdigest()
        if ledger[i]["current_hash"] != expected_hash:
             return {"status": "corrupted", "index": i}

    return {"status": "valid", "length": len(ledger)}

if __name__ == "__main__":
    import uvicorn
    import sys
    port = 8000
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    uvicorn.run(app, host="0.0.0.0", port=port)
