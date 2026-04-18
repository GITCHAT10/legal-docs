from fastapi import FastAPI
from unified_suite.airports.router import router as airport_router
from unified_suite.seaports.router import router as seaport_router

app = FastAPI(title="Unified Airport and Port Suite", version="1.0.0")

app.include_router(airport_router, prefix="/airports", tags=["Airports"])
app.include_router(seaport_router, prefix="/seaports", tags=["Sea Ports"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Maldives Unified Airport and Port Suite"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
