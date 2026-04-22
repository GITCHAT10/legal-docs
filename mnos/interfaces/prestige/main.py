from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mnos.core.security.config import settings
from mnos.core.auth.router import router as auth_router
from mnos.interfaces.prestige.guests.router import router as guests_router
from mnos.modules.inn.reservations.router import router as reservations_router
from mnos.modules.aqua.transfers.router import router as transfers_router
from mnos.modules.fce.router.router import router as finance_router
from mnos.modules.inn.housekeeping.router import router as housekeeping_router
from mnos.modules.inn.maintenance.router import router as maintenance_router
from mnos.modules.inn.laundry.router import router as laundry_router
from mnos.core.events.websockets import router as ws_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}", tags=["auth"])
app.include_router(guests_router, prefix=f"{settings.API_V1_STR}/guests", tags=["guests"])
app.include_router(reservations_router, prefix=f"{settings.API_V1_STR}/reservations", tags=["reservations"])
app.include_router(transfers_router, prefix=f"{settings.API_V1_STR}/transfers", tags=["transfers"])
app.include_router(finance_router, prefix=f"{settings.API_V1_STR}/finance", tags=["finance"])
app.include_router(housekeeping_router, prefix=f"{settings.API_V1_STR}/housekeeping", tags=["housekeeping"])
app.include_router(maintenance_router, prefix=f"{settings.API_V1_STR}/maintenance", tags=["maintenance"])
app.include_router(laundry_router, prefix=f"{settings.API_V1_STR}/laundry", tags=["laundry"])
app.include_router(ws_router, tags=["events"])

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "PRESTIGE HOLIDAYS Core is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
