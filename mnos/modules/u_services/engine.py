import uuid

class EducationEngine:
    def __init__(self, core):
        self.core = core

    def enroll(self, actor_ctx: dict, enrollment_data: dict):
        return self.core.execute_commerce_action(
            "education.enrollment.create",
            actor_ctx,
            self._internal_enroll,
            enrollment_data
        )

    def _internal_enroll(self, data):
        enrollment = {
            "enrollment_id": f"EDU-{uuid.uuid4().hex[:6].upper()}",
            "course_id": data.get("course_id"),
            "student_id": self.core.guard.get_actor().get("identity_id"),
            "fee": data.get("fee"),
            "status": "ENROLLED"
        }
        self.core.events.publish("education.enrollment_confirmed", enrollment)
        return enrollment
