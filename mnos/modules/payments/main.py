from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI(title="MNOS PAYMENTS")

class Transaction(BaseModel):
    invoice_id: str
    amount: float
    method: str

@app.post("/api/payments/transactions")
async def create_transaction(transaction: Transaction):
    return {"status": "success", "transaction_id": f"TXN-{uuid.uuid4()}"}

@app.get("/health")
async def health():
    return {"status": "ok"}
