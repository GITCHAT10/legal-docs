from fastapi import FastAPI

app = FastAPI(title="MNOS API Gateway")

@app.get("/health")
async def health():
    return {"status": "ok"}
