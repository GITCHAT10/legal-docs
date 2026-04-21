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
from mnos.modules.ogx.exceptions import SecurityException, FinancialException, SovereignException

router = APIRouter(prefix="/ogx/v1", tags=["OGX"])

# In a real production system, these would be managed by a dependency injection
# system and backed by a database/cache, not as global in-memory singletons.
state_machine = OGXStateMachine()
orchestrator = OGXSessionOrchestrator(state_machine)
degradation_engine = OGXDegradationEngine(state_machine, orchestrator)
recovery_service = OGXServiceRecovery(state_machine)

@router.post("/sessions/precheck", response_model=PrecheckResponse)
async def precheck(request: PrecheckRequest):
    try:
        return orchestrator.precheck(request)
    except SecurityException as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(request: PrecheckRequest):
    try:
        return orchestrator.create_session(request)
    except SovereignException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except SecurityException as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/sessions/{id}/start")
async def start_session(id: str):
    try:
        result = orchestrator.start_session(id)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except SovereignException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except SecurityException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FinancialException as e:
        raise HTTPException(status_code=402, detail=str(e))

@router.post("/sessions/{id}/end")
async def end_session(id: str):
    try:
        result = orchestrator.end_session(id)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except SovereignException as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/sessions/{id}/status", response_model=SessionStatusResponse)
async def get_session_status(id: str):
    status = orchestrator.get_session_status(id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    return status

@router.post("/telemetry/ingest")
async def ingest_telemetry(data: TelemetryIngest):
    try:
        return orchestrator.ingest_telemetry(data)
    except SovereignException as e:
        raise HTTPException(status_code=403, detail=str(e))

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
