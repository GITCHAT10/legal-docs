from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .schemas import FootprintInput, FootprintResult
from .mris import calculate_footprint

app = FastAPI(title="Maldives Sovereign Cockpit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/calculate", response_model=FootprintResult)
async def calculate(input_data: FootprintInput):
    return calculate_footprint(input_data)

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0-sovereign"}
