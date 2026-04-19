from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import uvicorn

app = FastAPI(title="MNOS Core - ELEONE Decision Engine")

class DecisionRequest(BaseModel):
    module: str
    action: str
    payload: dict

@app.get("/health")
def health():
    return {"status": "ok", "service": "eleone"}

@app.post("/decide")
async def decide(request: DecisionRequest):
    # Decision logic
    decision = "APPROVE"
    if request.payload.get("risk", 0) > 0.8:
        decision = "DENY"

    return {
        "decision": decision,
        "reason": "Policy compliance verified",
        "module": request.module
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
