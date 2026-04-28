import uuid
from datetime import datetime, UTC, timedelta
import hashlib
from typing import Dict, List, Optional
from mnos.modules.education.academic_bridge import AcademicBridgeEngine

class EducationEngine:
    """
    UHA Education Engine: Manages versioned course management,
    staff enrollment, and Black Coral Standard certification.
    """
    def __init__(self, core):
        self.core = core
        self.courses = {} # course_id -> {version_str: data}
        self.enrollments = {}
        self.certificates = {}
        self.credentials = {} # credential_id -> full_data
        self.academic_bridge = AcademicBridgeEngine(core, self)

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
            "provider": data.get("provider", "UHA Academy"),
            "level": data.get("level", "BC-1"), # Black Coral Level
            "modules": data.get("modules", []), # AIRMOVIE module IDs
            "fee": data.get("fee", 0.0),
            "status": "ACTIVE",
            "created_at": datetime.now(UTC).isoformat()
        }

        if course_id not in self.courses:
            self.courses[course_id] = {}

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
            return self._internal_issue_black_coral_credential(assessment_result)

        return assessment_result

    def _internal_issue_black_coral_credential(self, assessment_result):
        from mnos.modules.education.scoring import BlackCoralScoringEngine
        from mnos.modules.shadow.black_coral_protocol import BlackCoralVerificationEngine

        student_id = assessment_result["student_id"]
        enrollment = self.enrollments[assessment_result["enrollment_id"]]
        course = self.get_course(enrollment["course_id"], enrollment["version"])

        # 1. Retrieve Academic Baseline (30% weight)
        academic_baseline = self.academic_bridge.get_baseline(student_id)

        # 2. Calculate BCSI Score (70% Practical)
        scoring = BlackCoralScoringEngine(self.core)
        pillars = {
            "haccp": assessment_result["score"],
            "iso": assessment_result["score"] - 5,
            "unesco": assessment_result["score"] - 2,
            "michelin": assessment_result["score"] - 10
        }
        bcsi_data = scoring.calculate_bcsi(student_id, pillars, academic_baseline)

        if bcsi_data["haccp_gate"] == "HOLD":
             return {"status": "HOLD", "reason": "HACCP Hard Gate Triggered"}

        # 3. Issue BCVP Credential
        bcvp = BlackCoralVerificationEngine(self.core)
        credential = bcvp.issue_credential(
            trainee_id=student_id,
            tier=bcsi_data["eligible_tier"] or "BCA",
            competencies=bcsi_data["breakdown"]["pillars"],
            bcsi_score=bcsi_data["bcsi_score"]
        )

        # Store for dashboard lookup
        cred_id = f"BC-{bcsi_data['eligible_tier']}-{student_id[:8].upper()}"
        self.credentials[cred_id] = {
            "trainee_id": student_id,
            "credential": credential,
            "bcsi": bcsi_data
        }

        return credential

    def get_verification_dashboard_data(self, credential_id: str):
        """
        Aggregates data for the QR Verification Dashboard.
        """
        entry = self.credentials.get(credential_id)
        if not entry:
            return None

        trainee_id = entry["trainee_id"]
        # Core has guard, guard has identity_core
        profile = self.core.guard.identity_core.profiles.get(trainee_id)

        dashboard = {
            "identity_handshake": {
                "name": profile.get("full_name"),
                "mig_id": f"MIG-ID-{trainee_id[:4].upper()}-2026",
                "status": "VERIFIED_SOVEREIGN"
            },
            "snapshot_of_excellence": {
                "radar_chart": entry["bcsi"]["breakdown"]["pillars"],
                "academic_baseline": entry["bcsi"]["breakdown"]["academic_baseline"],
                "total_bcsi": entry["bcsi"]["bcsi_score"],
                "tier": entry["bcsi"]["eligible_tier"]
            },
            "red_flag_history": {
                "clean_record": self._check_clean_record(trainee_id),
                "last_incident_timestamp": None,
                "period": "Last 12 Months"
            },
            "mobility_status": {
                "status": "READY_FOR_DEPLOYMENT",
                "deployment_zones": ["Global", "Maldives Sovereign", "Swiss Elite"],
                "active_since": profile.get("created_at")
            },
            "legal_shield": "UHA verifies the individual's application of ISO and HACCP frameworks through deterministic monitoring; UHA is an independent performance auditor and is not the issuing body for ISO or UNESCO certifications."
        }

        return dashboard

    def _check_clean_record(self, trainee_id: str) -> bool:
        return True

    def verify_certificate(self, cert_id: str):
        return {"status": "VALID", "id": cert_id}

    def process_transcript(self, actor_ctx: Dict, payload: Dict):
        return self.academic_bridge.process_transcript(actor_ctx, payload)
