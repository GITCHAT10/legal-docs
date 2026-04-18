from fastapi import FastAPI
import hashlib
import json
import os
import sys
import uvicorn

app = FastAPI(title="BUILDX shadow Service")

ledger = []

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/entry")
async def add_entry(data: dict):
    prev_hash = ledger[-1]["current_hash"] if ledger else "0"*64
    content = json.dumps(data, sort_keys=True) + prev_hash
    curr_hash = hashlib.sha256(content.encode()).hexdigest()
    entry = {"data": data, "previous_hash": prev_hash, "current_hash": curr_hash}
    ledger.append(entry)
    return entry

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    uvicorn.run(app, host="0.0.0.0", port=port)
