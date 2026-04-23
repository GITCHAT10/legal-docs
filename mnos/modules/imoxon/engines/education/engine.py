class EducationEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def process_enrollment(self, actor_ctx: dict, enrollment_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.education.enroll",
            actor_ctx,
            self._internal_process_enrollment,
            enrollment_data
        )

    def _internal_process_enrollment(self, enrollment_data: dict):
        course_id = enrollment_data.get("course_id")
        fee = enrollment_data.get("fee", 0)

        pricing = self.fce.price_order(fee)

        entry = {
            "student": self.guard.get_actor().get("identity_id"),
            "course": course_id,
            "pricing": pricing,
            "status": "ENROLLED"
        }
        self.events.publish("education.enrolled", entry)
        return entry
