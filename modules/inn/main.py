from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="MNOS Module - INN")

@app.get("/health")
def health():
    return {"status": "ok", "module": "inn"}

@app.post("/execute")
async def execute(request: dict):
    # Module specific execution logic
    return {"status": "EXECUTED", "module": "inn", "action": request.get("action")}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
