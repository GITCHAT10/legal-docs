class EnforcementEngine:
    """
    IMOXON LEX: Enforcement and escalation state machine.
    """
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events

    def escalate_overdue(self, entity_id: str, reason: str):
        case = {
            "entity": entity_id,
            "reason": reason,
            "level": "LEGAL_CASE",
            "court_ready": True
        }
        self.shadow.record_action("lex.case_escalated", case)
        self.events.trigger("CASE_CREATED", case)
        return case
