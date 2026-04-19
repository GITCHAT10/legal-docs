from fastapi import FastAPI, HTTPException
from .models.telemetry import FullTelemetry, BoatState
from .service.optimization import GeneticOptimizer
from .service.maintenance import PredictiveMaintenance
from .service.digital_twin import DigitalTwinSync
from .service.precision_control import PrecisionMonitor

app = FastAPI(title="MNOS Dredging Engine")

# Initialize services
optimizer = GeneticOptimizer()
maintenance = PredictiveMaintenance()
digital_twin = DigitalTwinSync()
precision = PrecisionMonitor()

# Global state (for demo purposes)
last_telemetry = None

@app.get("/health")
async def health():
    return {"status": "UP", "module": "dredging_engine"}

@app.post("/telemetry")
async def ingest_telemetry(data: FullTelemetry):
    global last_telemetry
    last_telemetry = data

    # Trigger side effects
    maintenance_status = maintenance.assess_risk(data.dragflow)
    dt_sync = digital_twin.sync_sedimentation(data.seafarer)

    return {
        "status": "RECEIVED",
        "maintenance": maintenance_status,
        "digital_twin": dt_sync
    }

@app.post("/optimize")
async def optimize_path(state: BoatState):
    if not state.current_path:
        raise HTTPException(status_code=400, detail="Initial path is required")

    optimized_path = optimizer.optimize(
        state.current_path,
        state.fuel_level,
        state.passenger_count
    )

    return {
        "optimized_path": optimized_path,
        "efficiency_gain": "simulated_gain_15%"
    }

@app.get("/maintenance/status")
async def get_maintenance_status():
    if not last_telemetry:
        return {"status": "NO_DATA"}
    return maintenance.assess_risk(last_telemetry.dragflow)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
