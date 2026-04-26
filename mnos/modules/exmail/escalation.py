from datetime import datetime, UTC
from typing import List, Dict
from mnos.modules.exmail.service import ConversationGraph

class EscalationEngine:
    """
    Escalation Engine for MAC EOS ExMail.
    Enforces P1/P2 response times and notifies Central Command.
    """
    CHAIN = [
        {"role": "dept", "timeout": 0, "channel": "push"},
        {"role": "duty_manager", "timeout": 5, "channel": "sms"},
        {"role": "central_command", "timeout": 10, "channel": "whatsapp+sms"}
    ]

    DIRECT_ESCALATION = ["guest_stranded", "safety_risk", "system_down", "vip_failure"]

    def __init__(self, shadow, event_bus):
        self.shadow = shadow
        self.event_bus = event_bus

    def run_check(self):
        """Background job to check for pending escalations."""
        pending_convs = self._get_pending_p1_p2()
        for conv in pending_convs:
            wait = datetime.now(UTC) - conv.last_activity_at
            wait_minutes = wait.total_seconds() / 60

            for step in self.CHAIN:
                if wait_minutes >= step["timeout"] and self._is_escalation_needed(conv, step["role"]):
                    self._notify(step["role"], conv)
                    conv.escalation_state = step["role"]

                    self.shadow.commit("escalation.triggered", conv.id, {
                        "role": step["role"],
                        "timeout": step["timeout"],
                        "wait_time": wait_minutes
                    })

                    if self.event_bus:
                        self.event_bus.publish("exmail.escalation", {
                            "conv_id": conv.id,
                            "escalated_to": step["role"]
                        })

    def _get_pending_p1_p2(self):
        return [c for c in ConversationGraph._conversations.values() if c.priority in ["P1", "P2"]]

    def _is_escalation_needed(self, conv, target_role):
        role_ranks = {"INIT": 0, "dept": 1, "duty_manager": 2, "central_command": 3}
        current_rank = role_ranks.get(conv.escalation_state, 0)
        target_rank = role_ranks.get(target_role, 0)
        return target_rank > current_rank

    def _notify(self, role: str, conv):
        print(f"[ESCALATION] Notifying {role} for conversation {conv.id} (Priority: {conv.priority})")
        # Actual notification logic (SMS/WhatsApp) would go here
