from fastapi import FastAPI
import uvicorn
import time

app = FastAPI(title="MNOS Core - SAL Audit Log")

logs = []

@app.get("/health")
def health():
    return {"status": "ok", "service": "sal"}

@app.post("/log")
async def log_action(payload: dict):
    entry = {"timestamp": time.time(), "payload": payload}
    logs.append(entry)
    return {"status": "logged"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
