from fastapi import FastAPI
import uvicorn

app = FastAPI(title="MNOS Module - INN")

@app.get("/health")
def health():
    return {"status": "ok", "module": "inn"}

@app.post("/execute")
async def execute(request: dict):
    # Module specific execution logic
    return {"status": "EXECUTED", "module": "inn", "action": request.get("action")}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
