from fastapi import FastAPI
from mnos.api.integration import router as integration_router
from mnos.api.policies import router as policies_router
from mnos.core.config import config

app = FastAPI(title="MNOS Gateway Mock")

# ONLY compliant routes are registered
app.include_router(integration_router)
app.include_router(policies_router)

@app.get("/mnos/integration/v1/health")
async def health():
    return {"success": True, "data": {"status": "healthy", "mode": config["mode"]}}

@app.get("/")
async def root():
    return {"message": "MNOS Gateway is running"}
