from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
import sys
import uuid
import time

app = FastAPI(title="BUILDX BFI Banking Adapter")

@app.get("/health")
def health():
    return {"status": "ok", "service": "bfi"}

@app.post("/transfer")
async def transfer(amount: float, currency: str, recipient: str):
    msg_id = str(uuid.uuid4())
    return {
        "status": "PENDING",
        "message_id": msg_id,
        "iso20022_payload": f"<Document>...</Document>",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)
