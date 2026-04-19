from fastapi import FastAPI, HTTPException
import uuid

app = FastAPI(title="MNOS ANALYTICS")

@app.get("/api/analytics/kpi")
async def get_kpi():
    return {"status": "success", "wait_time": "15m", "claims_efficiency": "92%"}

@app.get("/health")
async def health():
    return {"status": "ok"}
