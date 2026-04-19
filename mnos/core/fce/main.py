from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional, List
import uuid

app = FastAPI(title="MNOS FCE")

class InvoiceItem(BaseModel):
    code: str
    price: float

class CalculateRequest(BaseModel):
    items: List[InvoiceItem]
    patient_id: str
    insurance_id: Optional[str] = None

@app.post("/api/core/fce/calculate")
async def calculate(request: CalculateRequest):
    # Mock financial clearance logic
    # 10% Service Charge, 17% TGST as per Maldives tax logic
    subtotal = sum(item.price for item in request.items)
    service_charge = subtotal * 0.10
    tgst = (subtotal + service_charge) * 0.17
    total = subtotal + service_charge + tgst

    return {
        "status": "success",
        "subtotal": subtotal,
        "service_charge": service_charge,
        "tgst": tgst,
        "total": total,
        "currency": "MVR"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
