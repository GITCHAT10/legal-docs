from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI(title="MNOS IDENTITY_BRIDGE")

class NationalIDLookup(BaseModel):
    national_id: str

@app.post("/api/identity-bridge/lookup")
async def lookup_national_id(request: NationalIDLookup):
    # Mock e-Faas / National ID lookup
    if request.national_id == "A123456":
        return {
            "status": "success",
            "full_name": "Ahmed Mohamed",
            "dob": "1990-01-01",
            "gender": "M"
        }
    raise HTTPException(status_code=404, detail="National ID not found")

@app.get("/api/identity-bridge/practitioner-sync")
async def sync_practitioners():
    # Mock practitioner registry sync
    return {"status": "success", "synced_count": 150}

@app.get("/health")
async def health():
    return {"status": "ok"}
