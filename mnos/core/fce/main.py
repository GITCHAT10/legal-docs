from fastapi import FastAPI

app = FastAPI(title="MNOS FCE Core Service")

@app.get("/health")
async def health():
    return {"status": "ok"}
