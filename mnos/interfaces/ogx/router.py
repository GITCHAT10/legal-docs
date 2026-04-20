from fastapi import APIRouter, HTTPException
from mnos.modules.ogx.schemas import (
    PrecheckRequest, PrecheckResponse, TelemetryIngest,
    DegradationEvent, FailStopEvent, ServiceRecoveryTrigger,
    SessionCreateResponse, SessionStatusResponse, RecoveryQuorum
)
from mnos.modules.ogx.service import (
    OGXSessionOrchestrator, OGXDegradationEngine, OGXServiceRecovery
)
from mnos.modules.ogx.state import OGXStateMachine

router = APIRouter(prefix="/ogx/v1", tags=["OGX"])

# In a real production system, these would be managed by a dependency injection
# system and backed by a database/cache, not as global in-memory singletons.
state_machine = OGXStateMachine()
orchestrator = OGXSessionOrchestrator(state_machine)
degradation_engine = OGXDegradationEngine(state_machine, orchestrator)
recovery_service = OGXServiceRecovery(state_machine)

@router.post("/sessions/precheck", response_model=PrecheckResponse)
async def precheck(request: PrecheckRequest):
    return orchestrator.precheck(request)

@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(request: PrecheckRequest):
    if state_machine.is_fail_stop():
        raise HTTPException(status_code=403, detail="System in FAIL-STOP mode")
    return orchestrator.create_session(request)

@router.post("/sessions/{id}/start")
async def start_session(id: str):
    result = orchestrator.start_session(id)
    if "error" in result:
        # Use 403 for business rule violations like FAIL-STOP
        status_code = 403 if "FAIL-STOP" in result["error"] else 404
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result

@router.post("/sessions/{id}/end")
async def end_session(id: str):
    result = orchestrator.end_session(id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/sessions/{id}/status", response_model=SessionStatusResponse)
async def get_session_status(id: str):
    status = orchestrator.get_session_status(id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    return status

@router.post("/telemetry/ingest")
async def ingest_telemetry(data: TelemetryIngest):
    return orchestrator.ingest_telemetry(data)

@router.post("/events/degradation")
async def report_degradation(event: DegradationEvent):
    return degradation_engine.handle_degradation(event)

@router.post("/events/fail-stop")
async def report_fail_stop(event: FailStopEvent):
    return degradation_engine.handle_fail_stop(event)

@router.post("/service-recovery/trigger")
async def trigger_recovery(trigger: ServiceRecoveryTrigger):
    return recovery_service.trigger_lemonade_protocol(trigger)

@router.post("/service-recovery/recovery-quorum")
async def process_recovery_quorum(quorum: RecoveryQuorum):
    return recovery_service.process_recovery_quorum(quorum)
