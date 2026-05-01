from fastapi import APIRouter, Depends, HTTPException
from mnos.modules.ut_aeromarine.mission_schema import MissionType, AssetType

def create_utam_router(planner, get_actor_ctx):
    router = APIRouter(prefix="/utam", tags=["ut-aeromarine"])

    @router.post("/mission/create")
    async def create_mission(mission_type: MissionType, asset_type: AssetType, actor: dict = Depends(get_actor_ctx)):
        try:
            return await planner.create_mission(actor["identity_id"], mission_type, asset_type)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/mission/launch")
    async def launch_mission(mission_id: str, device_id: str, actor: dict = Depends(get_actor_ctx)):
        try:
            return await planner.launch_mission(mission_id, device_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router
