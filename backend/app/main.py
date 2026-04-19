from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .schemas import FootprintInput, FootprintResult
from .logic import calculate_footprint

app = FastAPI(title="Maldives Carbon Footprint Engine")

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
    return {"status": "healthy"}
