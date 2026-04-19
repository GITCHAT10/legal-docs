import os
from fastapi import FastAPI
from pydantic import BaseModel
import hashlib
import json
import uuid
import time
import uvicorn

app = FastAPI(title="MNOS Core - SHADOW Ledger")

ledger = []

class ShadowEnvelope(BaseModel):
    event_id: str
    decision: str
    result: str
    data: dict

@app.get("/health")
def health():
    return {"status": "ok", "service": "shadow"}

@app.post("/commit")
async def commit(envelope: ShadowEnvelope):
    shadow_id = str(uuid.uuid4())
    prev_hash = ledger[-1]["audit_hash"] if ledger else "0"*64

    audit_content = f"{shadow_id}|{envelope.event_id}|{envelope.decision}|{prev_hash}"
    audit_hash = hashlib.sha256(audit_content.encode()).hexdigest()

    entry = {
        "shadow_id": shadow_id,
        "event_id": envelope.event_id,
        "decision": envelope.decision,
        "result": envelope.result,
        "audit_hash": audit_hash,
        "timestamp": time.time()
    }
    ledger.append(entry)
    return entry

@app.get("/audit/{shadow_id}")
async def get_audit(shadow_id: str):
    for entry in ledger:
        if entry["shadow_id"] == shadow_id:
            return entry
    return {"error": "not found"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
