from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="MNOS Core - EVENTS")

@app.get("/health")
def health():
    return {"status": "ok", "service": "events"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
