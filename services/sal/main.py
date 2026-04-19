from fastapi import FastAPI
import uvicorn
import os
import sys

app = FastAPI(title="BUILDX SAL")

@app.get("/health")
def health():
    return {"status": "ok", "service": "sal"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
