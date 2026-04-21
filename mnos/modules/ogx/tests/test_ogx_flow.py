import pytest
from datetime import datetime
from unittest.mock import MagicMock
from mnos.modules.ogx.schemas import (
    PrecheckRequest, DeviceContext, OGXState, TelemetryIngest, SensorPacket,
    DegradationEvent, FailStopEvent, RecoveryQuorum, RecoveryApproval
)
from mnos.modules.ogx.state import OGXStateMachine
from mnos.modules.ogx.service import (
    OGXSessionOrchestrator, OGXDegradationEngine, OGXServiceRecovery
)
from mnos.modules.ogx.exceptions import SecurityException, FinancialException, SovereignException

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

def test_precheck_unverified_guest(orchestrator):
    orchestrator.aegis.verify_guest = MagicMock(return_value=False)
    request = PrecheckRequest(
        resort_id="JUM-OLH",
        guest_id="UNKNOWN_GUEST",
        channel="resort_app",
        requested_slot=datetime.now(),
        package_code="OGX_SUNSET_45",
        device_context=DeviceContext(app_id="x", source_ip="y", client_version="z")
    )
    with pytest.raises(SecurityException):
        orchestrator.precheck(request)

def test_session_creation_unverified_guest(orchestrator):
    orchestrator.aegis.verify_guest = MagicMock(return_value=False)
    request = PrecheckRequest(
        resort_id="JUM-OLH",
        guest_id="UNKNOWN_GUEST",
        channel="resort_app",
        requested_slot=datetime.now(),
        package_code="OGX_SUNSET_45",
        device_context=DeviceContext(app_id="x", source_ip="y", client_version="z")
    )
    with pytest.raises(SecurityException):
        orchestrator.create_session(request)

def test_start_session_preauth_fail(orchestrator):
    request = PrecheckRequest(
        resort_id="JUM-OLH",
        guest_id="G1",
        channel="app",
        requested_slot=datetime.now(),
        package_code="P1",
        device_context=DeviceContext(app_id="x", source_ip="y", client_version="z")
    )
    orchestrator.aegis.verify_guest = MagicMock(return_value=True)
    create_res = orchestrator.create_session(request)
    session_id = create_res["session_id"]

    orchestrator.fce.preauthorize = MagicMock(return_value=False)
    with pytest.raises(FinancialException):
        orchestrator.start_session(session_id)

    assert orchestrator.get_session_status(session_id)["status"] == "BLOCKED"

def test_fail_stop_hard_lock(degradation_engine, state_machine, orchestrator):
    degradation_engine.handle_fail_stop(FailStopEvent(hub_id="H1", reason_code="F", actions=[]))
    assert state_machine.is_fail_stop()

    request = PrecheckRequest(
        resort_id="JUM-OLH",
        guest_id="G1",
        channel="app",
        requested_slot=datetime.now(),
        package_code="P1",
        device_context=DeviceContext(app_id="x", source_ip="y", client_version="z")
    )

    with pytest.raises(SovereignException, match="FAIL-STOP mode"):
        orchestrator.create_session(request)

    with pytest.raises(SovereignException, match="FAIL-STOP mode"):
        orchestrator.start_session("any")

    with pytest.raises(SovereignException, match="FAIL-STOP mode"):
        orchestrator.end_session("any")

def test_recovery_quorum_fail_same_role(degradation_engine, state_machine, recovery_service):
    degradation_engine.handle_fail_stop(FailStopEvent(hub_id="H1", reason_code="F", actions=[]))

    quorum = RecoveryQuorum(approvals=[
        RecoveryApproval(operator_id="OP1", role="ENGINEER", signature="s1"),
        RecoveryApproval(operator_id="OP2", role="engineer", signature="s2"),
        RecoveryApproval(operator_id="OP3", role="Engineer", signature="s3")
    ])
    res = recovery_service.process_recovery_quorum(quorum)
    assert res["status"] == "PENDING"
    assert res["valid_approvals_count"] == 1
    assert state_machine.is_fail_stop()

def test_recovery_quorum_success_distinct_roles(degradation_engine, state_machine, recovery_service):
    degradation_engine.handle_fail_stop(FailStopEvent(hub_id="H1", reason_code="F", actions=[]))

    quorum = RecoveryQuorum(approvals=[
        RecoveryApproval(operator_id="OP1", role="CFO", signature="s1"),
        RecoveryApproval(operator_id="OP2", role="CTO", signature="s2"),
        RecoveryApproval(operator_id="OP3", role="AUDITOR", signature="s3")
    ])
    res = recovery_service.process_recovery_quorum(quorum)
    assert res["status"] == "RECOVERED"
    assert state_machine.is_optimal()
