import uuid
from datetime import datetime, UTC
import hashlib

class EducationEngine:
    def __init__(self, core):
        self.core = core
        self.courses = {} # course_id -> {version_str: data}
        self.enrollments = {}
        self.certificates = {}

    def create_course(self, actor_ctx: dict, course_data: dict):
        return self.core.execute_commerce_action(
            "education.course.create",
            actor_ctx,
            self._internal_create_course,
            course_data
        )

    def _internal_create_course(self, data):
        course_id = data.get("course_id") or f"CRS-{uuid.uuid4().hex[:6].upper()}"
        version = data.get("version", "1.0.0")

        course_entry = {
            "course_id": course_id,
            "version": version,
            "title": data.get("title"),
            "provider": data.get("provider", "MARS Academy"),
            "level": data.get("level", "L1"),
            "modules": data.get("modules", []), # AIRMOVIE module IDs
            "fee": data.get("fee", 0.0),
            "status": "ACTIVE",
            "created_at": datetime.now(UTC).isoformat()
        }

        if course_id not in self.courses:
            self.courses[course_id] = {}

        # Deprecate existing versions of this course
        for v in self.courses[course_id]:
            self.courses[course_id][v]["status"] = "DEPRECATED"

        self.courses[course_id][version] = course_entry
        self.core.events.publish("education.course_created", {"id": course_id, "v": version})
        return course_entry

    def get_courses(self, active_only: bool = True):
        flat_list = []
        for cid in self.courses:
            for v in self.courses[cid]:
                if active_only and self.courses[cid][v]["status"] != "ACTIVE":
                    continue
                flat_list.append(self.courses[cid][v])
        return flat_list

    def get_course(self, course_id: str, version: str = None):
        versions = self.courses.get(course_id)
        if not versions:
            return None
        if version:
            return versions.get(version)
        # Get active or latest
        for v in versions:
            if versions[v]["status"] == "ACTIVE":
                return versions[v]
        return versions[sorted(versions.keys())[-1]]

    def enroll(self, actor_ctx: dict, enrollment_data: dict):
        return self.core.execute_commerce_action(
            "education.enrollment.create",
            actor_ctx,
            self._internal_enroll,
            enrollment_data
        )

    def _internal_enroll(self, data):
        course_id = data.get("course_id")
        student_id = data.get("student_id") or self.core.guard.get_actor().get("identity_id")

        course = self.get_course(course_id, data.get("version"))
        if not course:
            raise ValueError(f"Course {course_id} not found")

        enrollment_id = f"ENR-{uuid.uuid4().hex[:6].upper()}"
        enrollment = {
            "enrollment_id": enrollment_id,
            "course_id": course_id,
            "version": course["version"],
            "student_id": student_id,
            "fee": data.get("fee", course["fee"]),
            "status": "ENROLLED",
            "enrolled_at": datetime.now(UTC).isoformat()
        }
        self.enrollments[enrollment_id] = enrollment
        self.core.events.publish("education.enrollment_confirmed", enrollment)
        return enrollment

    def submit_assessment(self, actor_ctx: dict, assessment_data: dict):
        return self.core.execute_commerce_action(
            "education.assessment.submit",
            actor_ctx,
            self._internal_submit_assessment,
            assessment_data
        )

    def _internal_submit_assessment(self, data):
        enrollment_id = data.get("enrollment_id")
        enrollment = self.enrollments.get(enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment {enrollment_id} not found")

        score = data.get("score", 0)
        passing_score = 80

        assessment_result = {
            "assessment_id": f"ASM-{uuid.uuid4().hex[:6].upper()}",
            "enrollment_id": enrollment_id,
            "student_id": enrollment["student_id"],
            "score": score,
            "passed": score >= passing_score,
            "submitted_at": datetime.now(UTC).isoformat()
        }

        self.core.events.publish("education.assessment_submitted", assessment_result)

        if assessment_result["passed"]:
            return self._internal_generate_certificate(assessment_result)

        return assessment_result

    def _internal_generate_certificate(self, assessment_result):
        enrollment = self.enrollments[assessment_result["enrollment_id"]]
        course = self.get_course(enrollment["course_id"], enrollment["version"])

        cert_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"

        # Forensic hash for SHADOW verification
        raw_proof = f"{cert_id}|{assessment_result['student_id']}|{course['course_id']}|{course['version']}"
        forensic_hash = hashlib.sha256(raw_proof.encode()).hexdigest()

        certificate = {
            "certificate_id": cert_id,
            "student_id": assessment_result["student_id"],
            "course_id": course["course_id"],
            "course_version": course["version"],
            "course_title": course["title"],
            "issued_at": datetime.now(UTC).isoformat(),
            "forensic_hash": forensic_hash,
            "status": "VALID"
        }

        self.certificates[cert_id] = certificate

        # Explicitly log to SHADOW for forensic audit
        self.core.shadow.commit(
            "education.certificate.issued",
            assessment_result["student_id"],
            {
                "certificate_id": cert_id,
                "forensic_hash": forensic_hash,
                "course_id": course["course_id"],
                "course_version": course["version"]
            }
        )

        return certificate

    def verify_certificate(self, cert_id: str):
        cert = self.certificates.get(cert_id)
        if not cert:
            return {"status": "INVALID", "reason": "Not found"}

        return {"status": "VERIFIED", "details": cert}
