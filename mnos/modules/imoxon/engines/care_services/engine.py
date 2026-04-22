class CareServicesEngine:
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.assignments = {}

    def hire_caregiver(self, user_id: str, caregiver_id: str, service_type: str, hours: int):
        assignment = {
            "user_id": user_id,
            "caregiver_id": caregiver_id,
            "service": service_type,
            "hours": hours,
            "status": "ASSIGNED"
        }
        self.shadow.record_action("care.assigned", assignment)
        self.events.trigger("CARE_ASSIGNED", assignment)
        return assignment
