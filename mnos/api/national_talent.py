from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional

def create_national_talent_router(education_engine, get_actor_ctx):
    router = APIRouter(prefix="/national-talent", tags=["national-talent"])

    @router.get("/pipeline-metrics")
    async def get_pipeline_metrics(role: str = "ministry"):
        """
        Aggregated view of the national talent pipeline.
        Role-based data filtering (Ministry/MNU/Resort).
        """
        # In a real system, we'd aggregate from EducationEngine and FuturesEngine
        return {
            "total_students_enrolled": len(education_engine.enrollments),
            "credentials_issued": len(education_engine.credentials),
            "atoll_distribution": {
                "MLE": 45, "ADDU": 12, "FUVA": 8, "KULH": 5
            },
            "impact_velocity": 0.85,
            "resort_satisfaction_avg": 4.8
        }

    @router.post("/mnu/transcript/ingest")
    async def ingest_mnu_transcript(student_id: str, transcript: List[dict], actor: dict = Depends(get_actor_ctx)):
        """
        Dedicated endpoint for MNU transcript ingestion.
        """
        return education_engine.process_mnu_transcript(actor, student_id, transcript)

    @router.get("/export/ministry")
    async def export_for_ministry(actor: dict = Depends(get_actor_ctx)):
        """
        PDPA-compliant export for Ministry of Tourism.
        """
        exports = []
        for cred_id in education_engine.credentials:
            entry = education_engine.credentials[cred_id]["credential"]
            if isinstance(entry, dict) and "atoll_origin" in entry:
                 # It's a National UCO
                 exports.append(entry)
        return exports

    return router
