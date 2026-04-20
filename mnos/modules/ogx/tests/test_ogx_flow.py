import pytest
from datetime import datetime
from mnos.modules.ogx.schemas import (
    PrecheckRequest, DeviceContext, OGXState, TelemetryIngest, SensorPacket,
    DegradationEvent, FailStopEvent, RecoveryQuorum, RecoveryApproval
)
from mnos.modules.ogx.state import OGXStateMachine
from mnos.modules.ogx.service import (
    OGXSessionOrchestrator, OGXDegradationEngine, OGXServiceRecovery
)

@pytest.fixture
def state_machine():
    return OGXStateMachine()

@pytest.fixture
def orchestrator(state_machine):
    return OGXSessionOrchestrator(state_machine)

@pytest.fixture
def degradation_engine(state_machine, orchestrator):
    return OGXDegradationEngine(state_machine, orchestrator)

@pytest.fixture
def recovery_service(state_machine):
    return OGXServiceRecovery(state_machine)

def test_precheck_optimal(orchestrator):
    request = PrecheckRequest(
        resort_id="JUM-OLH",
        guest_id="AEGIS_GUEST_001",
        channel="resort_app",
        requested_slot=datetime.now(),
        package_code="OGX_SUNSET_45",
        device_context=DeviceContext(
            app_id="jumeirah-ogx",
            source_ip="127.0.0.1",
            client_version="1.0.0"
        )
    )
    response = orchestrator.precheck(request)
    assert response.status == "approved"
    assert response.session_state == OGXState.OPTIMAL
    assert response.price.total == 321.75

def test_session_lifecycle(orchestrator):
    request = PrecheckRequest(
        resort_id="JUM-OLH",
        guest_id="AEGIS_GUEST_001",
        channel="resort_app",
        requested_slot=datetime.now(),
        package_code="OGX_SUNSET_45",
        device_context=DeviceContext(
            app_id="jumeirah-ogx",
            source_ip="127.0.0.1",
            client_version="1.0.0"
        )
    )
    # 1. Create
    create_res = orchestrator.create_session(request)
    session_id = create_res["session_id"]
    assert create_res["status"] == "CREATED"

    # 2. Start
    start_res = orchestrator.start_session(session_id)
    assert start_res["status"] == "ACTIVE"

    # 3. Status
    status = orchestrator.get_session_status(session_id)
    assert status["status"] == "ACTIVE"
    assert status["guest_id"] == "AEGIS_GUEST_001"

    # 4. End
    end_res = orchestrator.end_session(session_id)
    assert end_res["status"] == "COMPLETED"

    final_status = orchestrator.get_session_status(session_id)
    assert final_status["status"] == "COMPLETED"
    assert final_status["end_time"] is not None

def test_degradation_flow(degradation_engine, state_machine):
    event = DegradationEvent(
        session_id="OGX_SESS_1001",
        new_state=OGXState.DEGRADED,
        reason_code="TELEMETRY_DRIFT",
        severity="HIGH",
        actions=["disable_replay", "freeze_esg_minting"]
    )
    response = degradation_engine.handle_degradation(event)
    assert response["new_state"] == OGXState.DEGRADED
    assert state_machine.is_degraded()

def test_fail_stop_and_recovery_quorum(degradation_engine, state_machine, orchestrator, recovery_service):
    # 1. Trigger fail-stop
    event = FailStopEvent(
        hub_id="JUM-OLH-HUB-01",
        reason_code="FISCAL_MISMATCH",
        actions=["lock_dispenser"]
    )
    degradation_engine.handle_fail_stop(event)
    assert state_machine.is_fail_stop()

    # 2. Precheck should be denied
    request = PrecheckRequest(
        resort_id="JUM-OLH",
        guest_id="AEGIS_GUEST_002",
        channel="resort_app",
        requested_slot=datetime.now(),
        package_code="OGX_SUNSET_45",
        device_context=DeviceContext(
            app_id="jumeirah-ogx",
            source_ip="127.0.0.1",
            client_version="1.0.0"
        )
    )
    response = orchestrator.precheck(request)
    assert response.status == "denied"

    # 3. Recovery Quorum (Insufficient)
    quorum_insufficient = RecoveryQuorum(approvals=[
        RecoveryApproval(operator_id="OP_CFO", role="CFO", signature="sig1"),
        RecoveryApproval(operator_id="OP_CTO", role="CTO", signature="sig2")
    ])
    res_insufficient = recovery_service.process_recovery_quorum(quorum_insufficient)
    assert res_insufficient["status"] == "PENDING"
    assert res_insufficient["valid_approvals_count"] == 2
    assert state_machine.is_fail_stop()

    # 4. Recovery Quorum (Sufficient)
    quorum_sufficient = RecoveryQuorum(approvals=[
        RecoveryApproval(operator_id="OP_CFO", role="CFO", signature="sig1"),
        RecoveryApproval(operator_id="OP_CTO", role="CTO", signature="sig2"),
        RecoveryApproval(operator_id="OP_ENG", role="Engineer", signature="sig3")
    ])
    res_sufficient = recovery_service.process_recovery_quorum(quorum_sufficient)
    assert res_sufficient["status"] == "RECOVERED"
    assert state_machine.is_optimal()

    # 5. System now accepts precheck
    response_after = orchestrator.precheck(request)
    assert response_after.status == "approved"
