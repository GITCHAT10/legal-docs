from fastapi import FastAPI, HTTPException
from .models.telemetry import FullTelemetry, BoatState
from .service.optimization import GeneticOptimizer
from .service.maintenance import PredictiveMaintenance
from .service.digital_twin import DigitalTwinSync
from .service.precision_control import PrecisionMonitor
from .service.safety import SafetyService
from ...shared.sdk.mnos_client import MnosClient
import uuid

app = FastAPI(title="MNOS Dredging Engine (Compliant)")

# Initialize services
optimizer = GeneticOptimizer()
maintenance = PredictiveMaintenance()
digital_twin = DigitalTwinSync()
precision = PrecisionMonitor()
safety = SafetyService()
mnos = MnosClient()

@app.get("/health")
async def health():
    return {"status": "UP", "module": "dredging_engine", "compliance": "MNOS.SHADOW"}

@app.post("/telemetry")
async def ingest_telemetry(data: FullTelemetry):
    trace_id = data.trace_id

    # 1. AEGIS verify (Safety)
    safety_check = safety.verify_operation(data)
    if not safety_check["allowed"]:
        # Log failure to SHADOW even on blocked requests
        mnos.shadow.commit({"safety_failure": safety_check}, trace_id)
        await mnos.events.publish("PUMP_ALERT", {"reason": safety_check["reason"]}, trace_id)
        raise HTTPException(status_code=403, detail=safety_check)

    # 2. ELEONE decide (Decision logic)
    # In this case, we decide to proceed with ingestion
    decision = {"status": "APPROVED", "action": "INGEST_DATA"}

    # 3. Logic Execution
    maintenance_status = maintenance.assess_risk(data.dragflow)
    dt_sync = digital_twin.sync_sedimentation(data.seafarer)

    # 4. EVENTS publish
    await mnos.events.publish("DEPTH_CHANGED", {"z_depth": data.dredgepack.z_depth}, trace_id)

    # 5. SHADOW commit
    audit_hash = mnos.shadow.commit(data.model_dump(), trace_id)

    # 6. FCE calculate
    # Simulate usage based on machine hours (random for demo)
    ledger = mnos.fce.calculate_ledger(fuel_usage=2.5, machine_hours=1.0, trace_id=trace_id)

    return {
        "status": "APPROVED",
        "trace_id": trace_id,
        "shadow_id": audit_hash,
        "maintenance": maintenance_status,
        "digital_twin": dt_sync,
        "fce_ledger": ledger
    }

@app.post("/optimize")
async def optimize_path(state: BoatState):
    trace_id = state.trace_id

    # Follow MNOS sequence for optimization
    # AEGIS verify -> ELEONE decide -> Execution -> EVENTS -> SHADOW -> FCE

    # Decision
    optimized_path = optimizer.optimize(
        state.current_path,
        state.fuel_level,
        state.passenger_count
    )

    await mnos.events.publish("ROUTE_OPTIMIZED", {"path_length": len(optimized_path)}, trace_id)
    audit_hash = mnos.shadow.commit({"original": state.current_path, "optimized": optimized_path}, trace_id)

    return {
        "status": "APPROVED",
        "trace_id": trace_id,
        "shadow_id": audit_hash,
        "optimized_path": optimized_path
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
