from fastapi import FastAPI

app = FastAPI(title="MNOS SHADOW Core Service")

@app.get("/health")
async def health():
    return {"status": "ok"}
