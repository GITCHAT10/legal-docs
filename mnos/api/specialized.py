from fastapi import APIRouter, Depends

def create_specialized_router(tourism, faith, transport, housing, exchange, get_actor_ctx):
    router = APIRouter(tags=["specialized"])

    @router.post("/tourism/book")
    async def book_tourism(data: dict, actor: dict = Depends(get_actor_ctx)):
        return tourism.book_package(actor, data)

    @router.post("/faith/donate")
    async def donate_faith(data: dict, actor: dict = Depends(get_actor_ctx)):
        return faith.donate(actor, data)

    @router.post("/transport/book")
    async def book_transport(data: dict, actor: dict = Depends(get_actor_ctx)):
        return transport.book_transport(actor, data)

    @router.post("/rent/lease")
    async def lease_housing(data: dict, actor: dict = Depends(get_actor_ctx)):
        return housing.create_lease(actor, data)

    @router.post("/exchange/transfer")
    async def transfer_exchange(data: dict, actor: dict = Depends(get_actor_ctx)):
        return exchange.transfer_asset(actor, data)

    return router
