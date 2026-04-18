from fastapi import FastAPI, HTTPException
import hashlib
import json
import os
import sys
import uvicorn
from typing import List, Dict

app = FastAPI(title="BUILDX shadow Service")

# In-memory ledger for blueprint purposes
# In production this would be backed by PostgreSQL or similar
ledger = []

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/entry")
async def add_entry(data: Dict):
    prev_hash = ledger[-1]["current_hash"] if ledger else "0"*64

    # Secure hash concatenation
    content = json.dumps(data, sort_keys=True) + prev_hash
    curr_hash = hashlib.sha256(content.encode()).hexdigest()

    entry = {
        "data": data,
        "previous_hash": prev_hash,
        "current_hash": curr_hash,
        "index": len(ledger)
    }
    ledger.append(entry)
    return entry

@app.get("/verify-integrity")
async def verify_integrity():
    errors = []
    for i in range(len(ledger)):
        entry = ledger[i]
        expected_prev = ledger[i-1]["current_hash"] if i > 0 else "0"*64

        if entry["previous_hash"] != expected_prev:
            errors.append(f"Hash mismatch at index {i}: expected previous {expected_prev}, got {entry['previous_hash']}")

        # Re-verify current hash
        content = json.dumps(entry["data"], sort_keys=True) + entry["previous_hash"]
        actual_hash = hashlib.sha256(content.encode()).hexdigest()
        if entry["current_hash"] != actual_hash:
            errors.append(f"Hash corrupted at index {i}: content does not match current_hash")

    if errors:
        return {"status": "corrupted", "errors": errors}
    return {"status": "valid", "count": len(ledger)}

@app.get("/ledger")
async def get_ledger():
    return ledger

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    uvicorn.run(app, host="0.0.0.0", port=port)
