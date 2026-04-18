from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict
import uuid

app = FastAPI(title="SAL Audit Log Service")

# Mock in-memory audit log
audit_logs = []

class AuditLogEntry(BaseModel):
    id: str
    timestamp: str
    service: str
    action: str
    payload: Dict

@app.get("/health")
async def health():
    return {"status": "ok", "service": "sal"}

@app.post("/log")
async def log_action(service: str, action: str, payload: Dict):
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "service": service,
        "action": action,
        "payload": payload
    }
    audit_logs.append(entry)
    return entry

@app.get("/query", response_model=List[AuditLogEntry])
async def query_logs():
    return audit_logs

if __name__ == "__main__":
    import uvicorn
    import sys
    port = 8000
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    uvicorn.run(app, host="0.0.0.0", port=port)
