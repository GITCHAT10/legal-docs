from fastapi import FastAPI
import uvicorn
import os
import sys

app = FastAPI(title="BUILDX Edge Node")

@app.get("/health")
def health():
    return {"status": "ok", "service": "edge-node"}

@app.post("/ingest")
async def ingest(data: dict):
    return {"status": "received", "data": data}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)
