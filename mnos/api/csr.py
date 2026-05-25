from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

class CsrReleaseRequest(BaseModel):
    bucket: str
    amount: float
    milestone: str

def create_csr_router(engine, get_actor_ctx):
    router = APIRouter(tags=["csr"])

    @router.get("/csr/report")
    async def get_csr_report(actor: dict = Depends(get_actor_ctx)):
        """CSR: Generate impact and allocation report."""
        with engine.guard.sovereign_context(actor):
            return engine.generate_impact_report()

    @router.post("/csr/release")
    async def release_csr_funds(req: CsrReleaseRequest, actor: dict = Depends(get_actor_ctx)):
        """CSR: Release funds to community projects."""
        return engine.release_funds(actor, req.bucket, req.amount, req.milestone)

    return router
