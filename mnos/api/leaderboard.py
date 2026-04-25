from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

def create_leaderboard_router(leaderboard_engine, get_actor_ctx):
    router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

    @router.get("/rankings/islands")
    async def get_island_rankings():
        return leaderboard_engine.get_island_rankings()

    @router.get("/rankings/hustlers")
    async def get_hustler_rankings(island: Optional[str] = None):
        return leaderboard_engine.get_top_hustlers(island)

    @router.get("/war-room/alerts")
    async def get_surge_alerts(actor: dict = Depends(get_actor_ctx)):
        if actor.get("role") not in ["admin", "island_gm"]:
            raise HTTPException(status_code=403, detail="Unauthorized for War Room alerts")
        return leaderboard_engine.surge_alerts

    return router
