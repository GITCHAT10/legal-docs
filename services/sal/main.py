from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
import sys
import uuid
import time
from typing import Dict

app = FastAPI(title="BUILDX SAL Standard Audit Log")

logs = []

@app.get("/health")
def health():
    return {"status": "ok", "service": "sal"}

@app.post("/log")
async def log_action(payload: dict):
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "payload": payload
    }
    logs.append(entry)
    return entry

@app.get("/query")
async def query():
    return logs[-100:]

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
