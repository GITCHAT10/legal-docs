import hashlib
import json
from datetime import datetime, UTC
from typing import Dict, List, Optional
from decimal import Decimal

class AcademicBridgeEngine:
    """
    Academic Bridge Engine: Ingests Swiss School transcripts and maps ECTS/Grades
    to the Black Coral academic baseline (30% weight).
    """

    def __init__(self, core, education_engine):
        self.core = core
        self.edu = education_engine
        self.academic_records = {} # trainee_id -> aggregated_academic_baseline

    def process_transcript(self, actor_ctx: Dict, payload: Dict):
        """
        Processes a transcript using the PARTNER-SCHOOL-COURSE-001 schema.
        """
        return self.core.execute_commerce_action(
            "education.academic.ingest",
            actor_ctx,
            self._internal_ingest,
            payload
        )

    def _internal_ingest(self, data):
        student_id = data.get("student_id")
        partner_code = data.get("partner_code", "GENERIC_PARTNER")
        courses = data.get("courses", [])

        # Calculate academic baseline based on grades and ECTS
        # Formula: Average (Grade / MaxGrade) * 100
        total_score = Decimal("0")
        count = 0

        for course in courses:
            grade = Decimal(str(course.get("grade", 0)))
            max_grade = Decimal(str(course.get("max_grade", 6.0))) # Swiss scale default
            total_score += (grade / max_grade) * 100
            count += 1

        baseline = float(total_score / count) if count > 0 else 0.0

        record = {
            "partner": partner_code,
            "ingested_at": datetime.now(UTC).isoformat(),
            "academic_baseline": baseline,
            "course_count": count,
            "status": "VERIFIED_ACADEMIC"
        }

        self.academic_records[student_id] = record

        self.core.events.publish("education.academic_ingested", {
            "student_id": student_id,
            "baseline": baseline
        })

        return record

    def get_baseline(self, student_id: str) -> float:
        return self.academic_records.get(student_id, {}).get("academic_baseline", 0.0)
