import uuid
from typing import Dict, List, Optional
from datetime import datetime
from mnos.modules.ogx.schemas import (
    PrecheckRequest, PrecheckResponse, OGXState, PriceInfo,
    SessionConstraints, TelemetryIngest, ServiceRecoveryTrigger,
    DegradationEvent, FailStopEvent, RecoveryQuorum
)
from mnos.modules.ogx.state import OGXStateMachine
from mnos.modules.ogx.adapters import (
    AegisAdapter, FceAdapter, EventsAdapter, ShadowAdapter, TerraformAdapter
)

class OGXSessionOrchestrator:
    def __init__(self, state_machine: OGXStateMachine):
        self.state_machine = state_machine
        self.aegis = AegisAdapter()
        self.fce = FceAdapter()
        self.events = EventsAdapter()
        self.shadow = ShadowAdapter()
        self.terraform = TerraformAdapter()
        self.active_sessions: Dict[str, Dict] = {}

    def precheck(self, request: PrecheckRequest) -> PrecheckResponse:
        # 1. verify guest with AEGIS
        self.aegis.verify_guest(request.guest_id)

        # 2. get FCE quote
        price_data = self.fce.get_quote(request.package_code)

        # 3. validate current hub state
        if self.state_machine.is_fail_stop():
            return PrecheckResponse(
                status="denied",
                session_state=self.state_machine.current_state,
                price=PriceInfo(**price_data),
                constraints=SessionConstraints(dispense_allowed=False)
            )

        return PrecheckResponse(
            status="approved",
            session_state=self.state_machine.current_state,
            price=PriceInfo(**price_data),
            constraints=SessionConstraints()
        )

    def create_session(self, request: PrecheckRequest):
        session_id = f"OGX_SESS_{uuid.uuid4().hex.upper()}"
        self.active_sessions[session_id] = {
            "status": "CREATED",
            "guest_id": request.guest_id,
            "package_code": request.package_code,
            "device_id": request.device_context.app_id
        }
        return {"session_id": session_id, "status": "CREATED"}

    def start_session(self, session_id: str):
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}

        if self.state_machine.is_fail_stop():
            return {"error": "System in FAIL-STOP mode"}

        session = self.active_sessions[session_id]

        # AEGIS verify device trust
        if not self.aegis.verify_device(session["device_id"]):
            return {"error": "Device trust validation failed"}

        # FCE preauth
        price_data = self.fce.get_quote(session["package_code"])
        self.fce.preauthorize(session_id, price_data["total"])

        # SHADOW log
        self.shadow.log_event("SESSION_START", {"session_id": session_id, "guest_id": session["guest_id"]})

        session["status"] = "ACTIVE"
        session["start_time"] = datetime.now()
        return {"session_id": session_id, "status": "ACTIVE"}

    def end_session(self, session_id: str):
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}

        session = self.active_sessions[session_id]
        # FCE post-folio
        price_data = self.fce.get_quote(session["package_code"])
        self.fce.post_folio(session_id, price_data["total"])

        # SHADOW log
        self.shadow.log_event("SESSION_END", {"session_id": session_id})

        session["status"] = "COMPLETED"
        session["end_time"] = datetime.now()
        return {"session_id": session_id, "status": "COMPLETED"}

    def get_session_status(self, session_id: str):
        if session_id not in self.active_sessions:
            return None
        session = self.active_sessions[session_id]
        return {
            "session_id": session_id,
            "status": session["status"],
            "start_time": session.get("start_time"),
            "end_time": session.get("end_time"),
            "guest_id": session["guest_id"]
        }

    def ingest_telemetry(self, data: TelemetryIngest):
        self.events.ingest_telemetry(data.model_dump())
        self.shadow.log_event("TELEMETRY", {"session_id": data.session_id, "sequence_hash": data.sequence_hash})
        return {"status": "received"}

class OGXDegradationEngine:
    def __init__(self, state_machine: OGXStateMachine, orchestrator: OGXSessionOrchestrator):
        self.state_machine = state_machine
        self.orchestrator = orchestrator
        self.events = EventsAdapter()
        self.shadow = ShadowAdapter()
        self.terraform = TerraformAdapter()

    def handle_degradation(self, event: DegradationEvent):
        self.state_machine.transition(OGXState.DEGRADED)
        self.events.record_state_change(event.session_id, "DEGRADED")
        self.shadow.log_event("DEGRADATION", event.model_dump())

        if "freeze_esg_minting" in event.actions:
            self.terraform.freeze_impact(event.session_id)

        return {"new_state": OGXState.DEGRADED}

    def handle_fail_stop(self, event: FailStopEvent):
        self.state_machine.transition(OGXState.FAIL_STOP)
        self.events.record_state_change(event.hub_id, "FAIL-STOP")
        self.shadow.log_event("FAIL_STOP", event.model_dump())

        # notify authorities as per specification
        self.events.emit_alert({"reason_code": event.reason_code, "severity": "FATAL", "recipients": ["CFO", "Auditor"]})

        return {"new_state": OGXState.FAIL_STOP}

class OGXServiceRecovery:
    def __init__(self, state_machine: OGXStateMachine):
        self.state_machine = state_machine
        self.shadow = ShadowAdapter()
        self.aegis = AegisAdapter()

    def trigger_lemonade_protocol(self, trigger: ServiceRecoveryTrigger):
        # Fan out
        self.shadow.log_event("SERVICE_RECOVERY_TRIGGERED", trigger.model_dump())
        return {
            "status": "recovery_initiated",
            "offer": trigger.recovery_offer,
            "guest_notified": True
        }

    def process_recovery_quorum(self, quorum: RecoveryQuorum):
        """
        Implementation of 3-of-4 approval logic for FAIL-STOP recovery.
        Enforces distinct operators and required roles.
        """
        required_roles = {"CFO", "CTO", "Auditor", "Engineer"}
        valid_approvals = {} # Using dict to ensure one approval per operator

        for approval in quorum.approvals:
            if approval.role in required_roles:
                if self.aegis.verify_operator(approval.operator_id):
                    valid_approvals[approval.operator_id] = approval

        if len(valid_approvals) >= 3:
            self.state_machine.transition(OGXState.OPTIMAL)
            self.shadow.notarize_recovery("SYSTEM", {"approvals": [a.model_dump() for a in valid_approvals.values()]})
            return {"status": "RECOVERED", "new_state": OGXState.OPTIMAL}

        return {"status": "PENDING", "valid_approvals_count": len(valid_approvals)}
