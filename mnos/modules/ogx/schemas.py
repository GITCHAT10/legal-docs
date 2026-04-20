from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class OGXState(str, Enum):
    OPTIMAL = "OPTIMAL"
    DEGRADED = "DEGRADED"
    FAIL_STOP = "FAIL-STOP"

class DeviceContext(BaseModel):
    app_id: str
    source_ip: str
    client_version: str

class PrecheckRequest(BaseModel):
    resort_id: str
    guest_id: str
    channel: str
    requested_slot: datetime
    package_code: str
    device_context: DeviceContext

class PriceInfo(BaseModel):
    currency: str = "USD"
    base: float
    service_charge: float
    tgst: float
    total: float

class SessionConstraints(BaseModel):
    price_floor_enforced: bool = True
    esg_mode: str = "active"
    dispense_allowed: bool = True

class PrecheckResponse(BaseModel):
    status: str
    session_state: OGXState
    price: PriceInfo
    constraints: SessionConstraints

class SessionCreateResponse(BaseModel):
    session_id: str
    status: str

class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    guest_id: str

class SensorPacket(BaseModel):
    vision_conf: float
    acoustic_conf: float
    imu_conf: float
    latency_ms: int
    drift_ms: int

class TelemetryIngest(BaseModel):
    session_id: str
    target_id: str
    timestamp: datetime
    context_segment: str = "VIP"
    sensor_packet: SensorPacket
    sequence_hash: str
    device_signature: str

class DegradationEvent(BaseModel):
    session_id: str
    new_state: OGXState
    reason_code: str
    severity: str
    actions: List[str]

class FailStopEvent(BaseModel):
    hub_id: str
    new_state: OGXState = OGXState.FAIL_STOP
    reason_code: str
    severity: str = "FATAL"
    actions: List[str]

class ServiceRecoveryTrigger(BaseModel):
    session_id: str
    guest_id: str
    failure_class: str
    recovery_offer: str
    approved_by: str

class RecoveryApproval(BaseModel):
    operator_id: str
    role: str # CFO, CTO, Auditor, Engineer
    signature: str

class RecoveryQuorum(BaseModel):
    approvals: List[RecoveryApproval]
