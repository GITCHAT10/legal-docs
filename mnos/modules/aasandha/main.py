from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uuid
from mnos.shared.sdk.client import MnosClient

app = FastAPI(title="MNOS AASANDHA")
mnos_client = MnosClient()

class Claim(BaseModel):
    patient_id: str
    service_code: str
    amount: float

@app.post("/api/aasandha/eligibility")
async def check_eligibility(national_id: str):
    # Mock eligibility check
    return {"eligible": True, "balance": 100000.0}

@app.post("/api/aasandha/claims")
async def submit_claim(claim: Claim):
    transaction_id = str(uuid.uuid4())
    # FCE check for insurance split
    fce_result = await mnos_client.calculate_fce({"items": [{"code": claim.service_code, "price": claim.amount}]})

    return {
        "status": "success",
        "transaction_id": transaction_id,
        "aasandha_share": fce_result.get("subtotal", 0) * 0.85,
        "patient_share": fce_result.get("subtotal", 0) * 0.15
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
