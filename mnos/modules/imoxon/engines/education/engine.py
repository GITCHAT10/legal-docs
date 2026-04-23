class EducationEngine:
    """
    Deduplicated: Institute Ops (Backend) + E-Academy (Learning Delivery).
    """
    def __init__(self, fce, shadow, events):
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def enroll_student(self, student_id: str, institute_id: str, course_id: str, fee: float):
        pricing = self.fce.price_order(fee)
        enrollment = {
            "student_id": student_id,
            "institute_id": institute_id,
            "course_id": course_id,
            "pricing": pricing,
            "status": "ENROLLED"
        }
        self.shadow.commit("edu.enrollment", enrollment)
        self.events.publish("CLASS_SCHEDULED", enrollment)
        return enrollment

    def log_attendance(self, student_id: str, course_id: str):
        # Delivery layer logic
        self.shadow.commit("edu.attendance", {"student": student_id, "course": course_id})
