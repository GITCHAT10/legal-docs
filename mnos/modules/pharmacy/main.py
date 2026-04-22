from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid

app = FastAPI(title="MNOS PHARMACY")

class Prescription(BaseModel):
    patient_id: str
    items: List[dict]

@app.post("/api/pharmacy/prescriptions")
async def create_prescription(prescription: Prescription):
    return {"status": "success", "prescription_id": f"RX-{uuid.uuid4()}"}

@app.post("/api/pharmacy/dispense")
async def dispense_medicine(prescription_id: str):
    return {"status": "success", "dispense_id": f"DSP-{uuid.uuid4()}"}

@app.get("/health")
async def health():
    return {"status": "ok"}
