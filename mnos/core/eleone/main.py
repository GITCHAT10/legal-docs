from fastapi import FastAPI

app = FastAPI(title="MNOS ELEONE Core Service")

@app.get("/health")
async def health():
    return {"status": "ok"}
