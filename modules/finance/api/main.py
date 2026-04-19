from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="MNOS Module - FINANCE")

@app.get("/health")
def health():
    return {"status": "ok", "module": "finance"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
