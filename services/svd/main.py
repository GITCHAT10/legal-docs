from fastapi import FastAPI
import uvicorn
import os
import sys

app = FastAPI(title="BUILDX SVD")

@app.get("/health")
def health():
    return {"status": "ok", "service": "svd"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
