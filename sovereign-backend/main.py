from fastapi import FastAPI, Body
from typing import List, Dict
import datetime

app = FastAPI(title="DMTE Sovereign Lite Backend")

# In-memory storage for MVP logs
dispatch_logs = []

@app.get("/health")
def health_check():
    return {"status": "online", "service": "sovereign-backend"}

@app.post("/sync-logs")
def sync_logs(logs: List[Dict] = Body(...)):
    global dispatch_logs
    for log in logs:
        log["synced_at"] = datetime.datetime.now().isoformat()
        dispatch_logs.append(log)
    return {"status": "success", "received": len(logs)}

@app.get("/dashboard-data")
def get_dashboard_data():
    total = len(dispatch_logs)
    verified = len([l for l in dispatch_logs if l.get("status") == "VERIFIED"])
    blocked = total - verified
    return {
        "total_dispatches": total,
        "verified": verified,
        "blocked": blocked,
        "last_sync": dispatch_logs[-1]["synced_at"] if dispatch_logs else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
