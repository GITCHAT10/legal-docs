from fastapi import FastAPI
from app.config import settings
from api import routes_clearance, routes_review, routes_inspection
from domain.database import init_db

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="MNOS Customs Command - State Integration Adapter"
)

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(routes_clearance.router, prefix=settings.API_PREFIX, tags=["Clearance"])
app.include_router(routes_review.router, prefix=settings.API_PREFIX, tags=["Review"])
app.include_router(routes_inspection.router, prefix=settings.API_PREFIX, tags=["Inspection"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {
        "module": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational"
    }
