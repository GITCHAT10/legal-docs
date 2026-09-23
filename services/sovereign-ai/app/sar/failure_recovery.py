from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable


class TimeoutClass(StrEnum):
    PRE_DISPATCH = "PRE_DISPATCH_TIMEOUT"
    ACKNOWLEDGED = "ACKNOWLEDGED_TIMEOUT"
    POST_EFFECT_RESPONSE_LOSS = "POST_EFFECT_RESPONSE_LOSS"
    DEPENDENCY = "DEPENDENCY_TIMEOUT"


class ExecutionState(StrEnum):
    NOT_DISPATCHED = "NOT_DISPATCHED"
    EXECUTION_UNKNOWN = "EXECUTION_UNKNOWN"
    EFFECT_CONFIRMED = "EFFECT_CONFIRMED"
    NO_EFFECT_CONFIRMED = "NO_EFFECT_CONFIRMED"
    H1_ESCALATION = "H1_ESCALATION"


@dataclass(frozen=True)
class RecoveryDecision:
    state: ExecutionState
    retry: bool
    verify_effect: bool
    escalate_h1: bool
    reason: str


class A17RecoveryHarness:
    """Deterministic recovery policy. Retrying an unknown effect without verification is forbidden."""

    def classify(self, timeout_class: TimeoutClass) -> RecoveryDecision:
        if timeout_class == TimeoutClass.PRE_DISPATCH:
            return RecoveryDecision(ExecutionState.NOT_DISPATCHED, True, False, False, "NO_DOWNSTREAM_RECEIPT")
        if timeout_class in {TimeoutClass.ACKNOWLEDGED, TimeoutClass.POST_EFFECT_RESPONSE_LOSS}:
            return RecoveryDecision(ExecutionState.EXECUTION_UNKNOWN, False, True, False, "VERIFY_EFFECT_REQUIRED")
        return RecoveryDecision(ExecutionState.EXECUTION_UNKNOWN, False, False, True, "AUTHORITATIVE_DEPENDENCY_UNAVAILABLE")

    def recover_unknown(
        self,
        verify_effect: Callable[[], bool | None],
        *,
        retry_count: int,
        max_retries: int = 1,
    ) -> RecoveryDecision:
        effect = verify_effect()
        if effect is True:
            return RecoveryDecision(ExecutionState.EFFECT_CONFIRMED, False, False, False, "DO_NOT_RETRY_EFFECT_EXISTS")
        if effect is False and retry_count < max_retries:
            return RecoveryDecision(ExecutionState.NO_EFFECT_CONFIRMED, True, False, False, "BOUNDED_RETRY_ALLOWED")
        if effect is False:
            return RecoveryDecision(ExecutionState.H1_ESCALATION, False, False, True, "RETRY_BUDGET_EXHAUSTED")
        return RecoveryDecision(ExecutionState.H1_ESCALATION, False, False, True, "EFFECT_VERIFICATION_INCONCLUSIVE")


class InjectedTransport:
    """Commissioning-only fault injector; never used as a production network adapter."""

    def __init__(self, timeout_class: TimeoutClass):
        self.timeout_class = timeout_class
        self.received = False
        self.effect_applied = False

    def dispatch(self, effect: Callable[[], None]) -> None:
        if self.timeout_class == TimeoutClass.PRE_DISPATCH:
            raise TimeoutError(self.timeout_class)
        self.received = True
        if self.timeout_class == TimeoutClass.ACKNOWLEDGED:
            raise TimeoutError(self.timeout_class)
        effect()
        self.effect_applied = True
        if self.timeout_class == TimeoutClass.POST_EFFECT_RESPONSE_LOSS:
            raise TimeoutError(self.timeout_class)
        if self.timeout_class == TimeoutClass.DEPENDENCY:
            raise TimeoutError(self.timeout_class)
