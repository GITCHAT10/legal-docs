from fastapi import APIRouter, Depends, Body
from typing import Dict, Any
from mnos.modules.prestige.flight_matrix.models import FlightMatrixDecision

def create_flight_matrix_router(matrix_engine, loader, recommender, recovery, get_actor_ctx):
    router = APIRouter(prefix="/flight-matrix", tags=["flight-matrix"])

    @router.post("/import")
    async def import_dataset(csv_content: str = Body(...), actor: dict = Depends(get_actor_ctx)):
        return loader.load_from_csv(actor, csv_content)

    @router.post("/evaluate", response_model=FlightMatrixDecision)
    async def evaluate_flight(context: Dict[str, Any], actor: dict = Depends(get_actor_ctx)):
        return matrix_engine.evaluate_feasibility(actor, context)

    @router.post("/recovery")
    async def get_recovery(decision: FlightMatrixDecision, actor: dict = Depends(get_actor_ctx)):
        return recovery.initiate_recovery(actor, decision)

    @router.post("/agent-portal/recommend-resorts")
    async def recommend_resorts(input_data: Dict[str, Any], actor: dict = Depends(get_actor_ctx)):
        return recommender.get_recommendations(actor, input_data)

    return router
