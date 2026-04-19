from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="MNOS Module - BFI")

@app.get("/health")
def health():
    return {"status": "ok", "module": "bfi"}

@app.post("/execute")
async def execute(request: dict):
    return {"status": "EXECUTED", "module": "bfi", "action": request.get("action")}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
