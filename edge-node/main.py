from fastapi import FastAPI, Query
from typing import Optional

app = FastAPI(title="DMTE Edge Node (LEN-01)")

@app.get("/health")
def health_check():
    return {"status": "online", "node_id": "LEN-01"}

@app.get("/compliance")
def get_compliance(vessel_id: str = Query(...)):
    # Mock data for MVP
    if vessel_id == "123":
        return {
            "vessel_id": vessel_id,
            "status": "CLEARED",
            "expiry": "2026-01-01"
        }
    else:
        return {
            "vessel_id": vessel_id,
            "status": "BLOCKED",
            "reason": "Vessel not in registry",
            "expiry": "N/A"
        }

@app.get("/environment")
def get_environment():
    # Mock data for MVP
    return {
        "location": "Jubail Jetty",
        "risk": 2,
        "weather": "Sunny",
        "timestamp": "2024-05-20T10:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
