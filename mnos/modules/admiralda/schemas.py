from typing import List, Optional, Any, Literal
from pydantic import BaseModel
from decimal import Decimal

class ParsedVoiceCommand(BaseModel):
    normalized_text: str
    intent: str
    confidence: float
    entities: dict[str, Any] = {}
    target_module: str | None = None
    requires_fce: bool = False
    risk_level: Literal["low", "medium", "high"] = "low"
    estimated_amount: Decimal | None = None

class VerifiedActor(BaseModel):
    actor_id: str
    tenant_id: str
    property_id: str | None = None
    roles: list[str]
    auth_strength: Literal["weak", "standard", "strong"]
    verification_confidence: float
    requires_step_up: bool = False

class PolicyDecision(BaseModel):
    allowed: bool
    decision: Literal["allow", "deny", "step_up_required", "human_review_required"]
    reason_code: str | None = None

class FcePrecheckResult(BaseModel):
    passed: bool
    transaction_id: str | None = None
    reason: str | None = None

class ModuleExecutionResult(BaseModel):
    success: bool
    target_module: str
    action: str
    record_id: str | None = None
    payload: dict[str, Any] = {}
    human_message: str

class ShadowCommitResult(BaseModel):
    success: bool
    commit_id: str | None = None

class CommandExecutionResult(BaseModel):
    status: Literal["accepted", "rejected", "failed"]
    command_id: str
    actor_id: str | None = None
    session_id: str
    transcript: str
    normalized_text: str
    intent: str | None = None
    target_module: str | None = None
    policy_decision: str
    reason_code: str | None = None
    requires_fce: bool = False
    fce_check_passed: bool | None = None
    shadow_commit_id: str | None = None
    events_emitted: list[str] = []
    execution_payload: dict[str, Any] = {}
    human_message: str
