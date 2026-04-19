from fastapi import FastAPI, HTTPException
import uuid

app = FastAPI(title="MNOS PUBLIC_HEALTH")

@app.get("/api/public-health/signals")
async def get_signals():
    return {"status": "success", "signals": [{"type": "ILI", "count": 12}]}

@app.get("/health")
async def health():
    return {"status": "ok"}
