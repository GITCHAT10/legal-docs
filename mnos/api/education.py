from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional

def create_education_router(education_engine, get_actor_ctx):
    router = APIRouter(prefix="/education", tags=["education"])

    @router.post("/courses/create")
    async def create_course(data: dict, actor: dict = Depends(get_actor_ctx)):
        return education_engine.create_course(actor, data)

    @router.get("/courses")
    async def list_courses():
        return education_engine.get_courses()

    @router.post("/enroll")
    async def enroll_education(data: dict, actor: dict = Depends(get_actor_ctx)):
        return education_engine.enroll(actor, data)

    @router.post("/assessment/submit")
    async def submit_assessment(data: dict, actor: dict = Depends(get_actor_ctx)):
        return education_engine.submit_assessment(actor, data)

    @router.get("/certificates/verify")
    async def verify_certificate(cert_id: str):
        return education_engine.verify_certificate(cert_id)

    @router.post("/academic/ingest")
    async def ingest_transcript(data: dict, actor: dict = Depends(get_actor_ctx)):
        return education_engine.process_transcript(actor, data)

    # --- UHA BLACK CORAL STANDARD: QR VERIFICATION ---
    @router.get("/bcs/verify/{credential_id}")
    async def verify_bcs_credential(credential_id: str):
        """
        Public Verification Endpoint for Recruiters and GMs.
        Returns the Live Performance Dashboard for a Black Coral holder.
        """
        dashboard_data = education_engine.get_verification_dashboard_data(credential_id)
        if not dashboard_data:
            raise HTTPException(status_code=404, detail="Credential not found or invalid.")

        return dashboard_data

    return router
