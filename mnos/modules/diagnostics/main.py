from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI(title="MNOS DIAGNOSTICS")

class DiagnosticOrder(BaseModel):
    patient_id: str
    test_codes: list

@app.post("/api/diagnostics/orders")
async def create_order(order: DiagnosticOrder):
    return {"status": "success", "order_id": f"ORD-{uuid.uuid4()}"}

@app.post("/api/diagnostics/results")
async def post_result(order_id: str, result_data: dict):
    return {"status": "success", "result_id": f"RES-{uuid.uuid4()}"}

@app.get("/health")
async def health():
    return {"status": "ok"}
