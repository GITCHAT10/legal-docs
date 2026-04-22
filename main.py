from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mnos.modules.elegal.anchor import legal_anchor
from mnos.modules.fce.service import fce
from decimal import Decimal

app = FastAPI(title="iGEO Nexus OS / eLEGAL")

class AnchorRequest(BaseModel):
    contract_id: str
    actor_id: str

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

@app.get("/health")
async def health():
    return {"status": "SOVEREIGN"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
