from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional

def create_futures_router(futures_engine, get_actor_ctx):
    router = APIRouter(prefix="/futures", tags=["futures"])

    @router.post("/apply")
    async def apply_to_futures(data: dict):
        """
        Public application endpoint for Black Coral Futures.
        """
        try:
            return futures_engine.submit_application(data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/impact-metrics")
    async def get_impact_metrics():
        """
        Public/Donor impact reporting endpoint.
        """
        return futures_engine.get_impact_metrics()

    @router.post("/deployment/record")
    async def record_deployment(applicant_id: str, resort_id: str, actor: dict = Depends(get_actor_ctx)):
        """
        Internal endpoint for recording trainee deployment.
        """
        try:
            return futures_engine.record_deployment(applicant_id, resort_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    return router
