from fastapi import FastAPI

app = FastAPI(title="MNOS AEGIS Core Service")

@app.get("/health")
async def health():
    return {"status": "ok"}
