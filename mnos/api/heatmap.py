from fastapi import APIRouter, Depends, HTTPException
from typing import List

def create_heatmap_router(heatmap_engine, get_actor_ctx):
    router = APIRouter(prefix="/national", tags=["national-intelligence"])

    @router.get("/summary")
    async def get_summary(actor: dict = Depends(get_actor_ctx)):
        """Aggregated Intelligence for planners."""
        return heatmap_engine.get_national_summary()

    @router.get("/map-data")
    async def get_map_data(actor: dict = Depends(get_actor_ctx)):
        """Interactive Map Layer Data."""
        return heatmap_engine.get_map_data()

    @router.get("/islands/{island_name}")
    async def get_island_detail(island_name: str, actor: dict = Depends(get_actor_ctx)):
        """Drill-down into island performance."""
        return heatmap_engine.drill_down(island_name)

    @router.get("/presidential/dashboard")
    async def get_presidential_dash(actor: dict = Depends(get_actor_ctx)):
        """CABINET-LEVEL-CONTROL: Executive Command View."""
        if actor.get("role") not in ["admin", "president", "cabinet"]:
             raise HTTPException(status_code=403, detail="Cabinet-level access required for National Health Dashboard")
        return heatmap_engine.get_presidential_executive_summary()

    return router
