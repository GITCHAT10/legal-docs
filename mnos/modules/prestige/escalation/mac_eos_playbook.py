from enum import Enum
from typing import Dict, Any, List

class EscalationState(str, Enum):
    ESCALATION_OPENED = "ESCALATION_OPENED"
    ESCALATION_OWNER_ASSIGNED = "ESCALATION_OWNER_ASSIGNED"
    RECOVERY_OPTIONS_GENERATED = "RECOVERY_OPTIONS_GENERATED"
    RECOVERY_PLAN_SELECTED = "RECOVERY_PLAN_SELECTED"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"
    HUMAN_APPROVAL_GRANTED = "HUMAN_APPROVAL_GRANTED"
    RECOVERY_PLAN_EXECUTED = "RECOVERY_PLAN_EXECUTED"
    STATUS_RETURNED_GREEN = "STATUS_RETURNED_GREEN"
    FINAL_24H_LOGISTICS_PROOF_RESEALED = "FINAL_24H_LOGISTICS_PROOF_RESEALED"

class MacEosPlaybook:
    def __init__(self, core):
        self.core = core
        self.escalations = {} # esc_id -> data

    def open_escalation(self, booking_id: str, reason: str, actor_ctx: dict):
        # no Red item can be hidden
        return self.core.execute_commerce_action(
            "prestige.escalation.open",
            actor_ctx,
            self._internal_open,
            booking_id, reason
        )

    def _internal_open(self, booking_id, reason):
        esc_id = f"ESC-{booking_id}"
        self.escalations[esc_id] = {
            "status": EscalationState.ESCALATION_OPENED,
            "reason": reason
        }
        return self.escalations[esc_id]
