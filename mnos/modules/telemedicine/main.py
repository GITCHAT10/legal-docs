from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI(title="MNOS TELEMEDICINE")

class SessionRequest(BaseModel):
    patient_id: str
    practitioner_id: str

@app.post("/api/telemedicine/sessions")
async def create_session(session: SessionRequest):
    return {"status": "success", "session_id": f"TEL-{uuid.uuid4()}"}

@app.get("/health")
async def health():
    return {"status": "ok"}
