from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="MNOS Core - AEGIS")

@app.get("/health")
def health():
    return {"status": "ok", "service": "aegis"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
