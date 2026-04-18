from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import redis
import json
import os

app = FastAPI(title="ELEONE Decision Engine")

# Redis Event Bus
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0
)

class ProcurementRequest(BaseModel):
    item: str
    quantity: int
    price: float
    vendor_id: str
    compliance_check: bool = True

class DecisionResponse(BaseModel):
    approved: bool
    reason: str
    transaction_id: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "ok", "service": "eleone"}

@app.post("/decide", response_model=DecisionResponse)
async def decide(request: ProcurementRequest):
    # Mock decision logic
    approved = True
    reason = "Criteria met"
    tx_id = f"TX-ELE-{os.urandom(4).hex()}"

    if request.price > 1000000:
        approved = False
        reason = "Price exceeds automatic approval threshold"

    if not request.compliance_check:
        approved = False
        reason = "Compliance check failed"

    # Emit Event to Redis
    event = {
        "event_type": "procurement.decision",
        "approved": approved,
        "item": request.item,
        "price": request.price,
        "tx_id": tx_id if approved else None,
        "timestamp": json.dumps(True) # Dummy timestamp
    }

    try:
        redis_client.publish("procurement.events", json.dumps(event))
    except Exception as e:
        print(f"Failed to publish event: {e}")

    return DecisionResponse(approved=approved, reason=reason, transaction_id=tx_id if approved else None)

if __name__ == "__main__":
    import uvicorn
    import sys
    port = 8000
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    uvicorn.run(app, host="0.0.0.0", port=port)
