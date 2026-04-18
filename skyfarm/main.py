from fastapi import FastAPI
from skyfarm.database import engine, Base
import skyfarm.identity.models
import skyfarm.marine.models
import skyfarm.agri.models
import skyfarm.logistics.models
import skyfarm.finance.models
import skyfarm.trace.models
import skyfarm.restaurant.models

# Create tables
Base.metadata.create_all(bind=engine)

from skyfarm.marine.router import router as marine_router
from skyfarm.logistics.router import router as logistics_router
from skyfarm.finance.router import router as finance_router
from skyfarm.trace.router import router as trace_router
from skyfarm.integration.router import router as integration_router

app = FastAPI(title="SKYFARM API Gateway")

app.include_router(marine_router)
app.include_router(logistics_router)
app.include_router(finance_router)
app.include_router(trace_router)
app.include_router(integration_router)

@app.get("/")
def read_root():
    return {"message": "SKYFARM API Gateway is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
