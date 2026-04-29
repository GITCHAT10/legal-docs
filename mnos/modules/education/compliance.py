from datetime import datetime, UTC

class ComplianceTriggerEngine:
    """
    Automated training assignment based on operational events.
    Connects iMOXON operational failures to MARS Academy retraining.
    """
    def __init__(self, core, education_engine):
        self.core = core
        self.edu = education_engine
        self.rules = {
            "haccp.violation": "L1-HACCP-REFRESH",
            "guest.complaint.communication": "L1-SERVICE-DNA",
            "security.incident.access": "L1-SECURITY-BASIC",
            "pms.void.unauthorized": "L2-FRONT-OFFICE-HARDENING"
        }

    def handle_operational_event(self, event_type: str, actor_id: str, metadata: dict):
        """
        Main entry point for external events.
        """
        module_id = self.rules.get(event_type)
        if not module_id:
            return None

        # Auto-assign retraining
        assignment = {
            "actor_id": actor_id,
            "trigger_event": event_type,
            "required_module": module_id,
            "assigned_at": datetime.now(UTC).isoformat(),
            "urgency": "HIGH",
            "reason": metadata.get("description", "Automatic compliance trigger")
        }

        # Committing to SHADOW via system context
        from mnos.shared.execution_guard import _sovereign_context
        sys_actor = {"identity_id": "SYSTEM", "device_id": "CORE-SRV", "role": "admin", "system_override": True}
        token = _sovereign_context.set({"token": "COMPLIANCE-TRIGGER", "actor": sys_actor})
        try:
            self.core.shadow.commit(
                "education.compliance.trigger",
                actor_id,
                assignment
            )

            # Logic to actually push this to the student's LMS dashboard
            self.edu.enroll(sys_actor, {"course_id": module_id, "student_id": actor_id})

        finally:
            _sovereign_context.reset(token)

        return assignment
