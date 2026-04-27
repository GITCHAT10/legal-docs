from fastapi import APIRouter, Depends, Header, HTTPException
from typing import List, Optional
from pydantic import BaseModel

class PlaybackRequest(BaseModel):
    content_id: str
    device_hash: str
    room_id: str

def create_airmovie_router(airmovie_engine, airmovie_sync, get_actor_ctx):
    router = APIRouter(prefix="/airmovie", tags=["airmovie"])

    @router.get("/catalog")
    async def get_catalog(room_id: Optional[str] = Query(None), actor: dict = Depends(get_actor_ctx)):
        return airmovie_engine.get_catalog(room_id=room_id)

    @router.post("/play")
    async def start_playback(req: PlaybackRequest, actor: dict = Depends(get_actor_ctx)):
        return airmovie_engine.start_playback(actor, req.content_id, req.device_hash)

    @router.post("/sync")
    async def sync_logs(actor: dict = Depends(get_actor_ctx)):
        # Only allow system/admin for sync trigger in real world
        count = airmovie_sync.sync_pending_logs()
        return {"synced_logs": count}

    @router.get("/status")
    async def get_status():
        return {"status": "EDGE_ACTIVE", "offline_ready": True}

    return router

# To fix the Query import issue
from fastapi import Query
