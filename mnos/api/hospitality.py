from fastapi import APIRouter, Depends, HTTPException

def create_hospitality_router(hospitality_engine, get_actor_ctx):
    router = APIRouter(prefix="/hospitality", tags=["hospitality"])

    @router.get("/properties")
    async def get_properties():
        return hospitality_engine.get_properties()

    @router.post("/properties/register")
    async def register_property(data: dict, actor: dict = Depends(get_actor_ctx)):
        return hospitality_engine.register_property(actor, data)

    @router.post("/book")
    async def book_stay(data: dict, actor: dict = Depends(get_actor_ctx)):
        try:
            return hospitality_engine.book_stay(actor, data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

    return router
