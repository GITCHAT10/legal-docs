from fastapi import FastAPI

app = FastAPI(title="MNOS EVENTS Core Service")

@app.get("/health")
async def health():
    return {"status": "ok"}
