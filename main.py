from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mnos.modules.elegal.anchor import legal_anchor
from mnos.modules.elegal.packs.tenancy import tenancy_engine
from mnos.modules.elegal.packs.tenancy_finance import tenancy_finance
from mnos.modules.fce.service import fce
from decimal import Decimal

app = FastAPI(title="iGEO Nexus OS / eLEGAL")

class AnchorRequest(BaseModel):
    contract_id: str
    actor_id: str

class LeaseRequest(BaseModel):
    landlord_id: str
    tenant_id: str
    property_id: str
    monthly_rent: float
    deposit: float

class RentPaymentRequest(BaseModel):
    lease_id: str
    amount: float

@app.post("/elegal/v1/anchor")
async def create_legal_anchor(request: AnchorRequest):
    """
    Sovereign Legal RC Gate: Mandatory contract-transaction binding.
    """
    try:
        anchor_id = legal_anchor.create_anchor(request.contract_id, request.actor_id)
        return {"anchor_id": anchor_id, "status": "LOCKED"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/elegal/v1/tenancy/lease")
async def create_lease(request: LeaseRequest):
    """
    Maldives Tenancy Pack: Creates lease bound to eLEGAL anchor.
    """
    try:
        lease = tenancy_engine.create_lease(
            request.landlord_id,
            request.tenant_id,
            request.property_id,
            request.monthly_rent,
            request.deposit
        )
        return lease
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/elegal/v1/tenancy/payment")
async def process_rent_payment(request: RentPaymentRequest):
    """
    Captures rent cashflow via FCE + Legal Anchor.
    """
    try:
        payment = tenancy_finance.process_rent_payment(request.lease_id, Decimal(str(request.amount)))
        return payment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "SOVEREIGN"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
