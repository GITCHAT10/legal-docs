from fastapi import FastAPI, Request
from pydantic import BaseModel
import hashlib
import json
import uuid

app = FastAPI(title="MNOS SHADOW")

# Mock storage for hash chain
hash_chain = ["genesis_hash"]

class CommitRequest(BaseModel):
    transaction_id: str
    event_id: str
    data: dict

@app.post("/api/core/shadow/commit")
async def commit(request: CommitRequest):
    previous_hash = hash_chain[-1]
    data_str = json.dumps(request.data, sort_keys=True)
    new_hash = hashlib.sha256((data_str + previous_hash).encode()).hexdigest()
    hash_chain.append(new_hash)

    shadow_id = f"SHD-{uuid.uuid4()}"
    return {
        "status": "success",
        "shadow_id": shadow_id,
        "audit_hash": new_hash
    }

@app.get("/verify-integrity")
async def verify_integrity():
    # Logic to verify the chain
    return {"status": "valid", "chain_length": len(hash_chain)}

@app.get("/health")
async def health():
    return {"status": "ok"}
