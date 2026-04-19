from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI(title="MNOS FINANCE")

class Invoice(BaseModel):
    patient_id: str
    items: list

@app.post("/api/finance/invoices")
async def create_invoice(invoice: Invoice):
    return {"status": "success", "invoice_id": f"INV-{uuid.uuid4()}"}

@app.get("/health")
async def health():
    return {"status": "ok"}
