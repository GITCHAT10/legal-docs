from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from decimal import Decimal
from enum import Enum
from datetime import datetime, UTC

class MNUProgram(str, Enum):
    DIPLOMA_HOSPITALITY = "diploma_hospitality"
    BA_TOURISM = "ba_tourism"
    CERTIFICATE_SERVICE = "certificate_service"

class MNUCourseMapping(BaseModel):
    """Maps MNU courses to Black Coral pillars"""
    mnu_program: MNUProgram
    course_code: str
    course_title: str
    mnu_credits: int
    maps_to_pillar: str  # "haccp", "iso", "unesco", "michelin"
    competency_weight: Decimal
    verification_required: bool
    shadow_audit_fields: List[str]

# Pre-configured mappings
MNU_MAPPINGS = {
    MNUProgram.DIPLOMA_HOSPITALITY: [
        MNUCourseMapping(
            mnu_program=MNUProgram.DIPLOMA_HOSPITALITY,
            course_code="MNU-HOSP101",
            course_title="Introduction to Hospitality Operations",
            mnu_credits=3,
            maps_to_pillar="iso",
            competency_weight=Decimal("0.70"),
            verification_required=True,
            shadow_audit_fields=["sop_completion_rate", "task_timing_variance"]
        ),
        MNUCourseMapping(
            mnu_program=MNUProgram.DIPLOMA_HOSPITALITY,
            course_code="MNU-HOSP205",
            course_title="Food Safety & Hygiene Management",
            mnu_credits=4,
            maps_to_pillar="haccp",
            competency_weight=Decimal("0.90"),
            verification_required=True,
            shadow_audit_fields=["temp_log_compliance", "ccp_breach_rate"]
        ),
    ]
}

class MNUBridgeEngine:
    """
    Academic Bridge for Maldives National University.
    Aligns MNU curriculum with UHA verification.
    """
    def __init__(self, core):
        self.core = core
        self.mappings = MNU_MAPPINGS
        self.academic_records = {} # student_id -> aligned_data

    def align_transcript(self, student_id: str, mnu_transcript: List[Dict]):
        """
        Calculates academic baseline specifically for MNU students.
        """
        pillar_baselines = {"haccp": 0, "iso": 0, "unesco": 0, "michelin": 0}
        counts = {"haccp": 0, "iso": 0, "unesco": 0, "michelin": 0}

        for item in mnu_transcript:
            code = item.get("course_code")
            grade = Decimal(str(item.get("grade", 0)))
            max_grade = Decimal(str(item.get("max_grade", 4.0))) # MNU might use 4.0 GPA

            # Find mapping
            mapping = self._find_mapping(code)
            if mapping:
                pillar = mapping.maps_to_pillar
                pillar_baselines[pillar] += float((grade / max_grade) * 100)
                counts[pillar] += 1

        # Average out
        final_baselines = {}
        for p in pillar_baselines:
            final_baselines[p] = pillar_baselines[p] / counts[p] if counts[p] > 0 else 0

        # Calculate overall academic baseline (30% weight component)
        overall = sum(final_baselines.values()) / 4

        result = {
            "student_id": student_id,
            "institution": "Maldives National University",
            "pillar_baselines": final_baselines,
            "overall_academic_baseline": overall,
            "aligned_at": datetime.now(UTC).isoformat()
        }

        self.academic_records[student_id] = result

        self.core.events.publish("education.academic_ingested", {
            "student_id": student_id,
            "baseline": overall,
            "institution": "MNU"
        })

        return result

    def _find_mapping(self, course_code: str) -> Optional[MNUCourseMapping]:
        for program in self.mappings:
            for mapping in self.mappings[program]:
                if mapping.course_code == course_code:
                    return mapping
        return None
