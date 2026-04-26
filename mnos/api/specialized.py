from fastapi import APIRouter, Depends

def create_specialized_router(tourism, faith, transport, housing, exchange, education, get_actor_ctx):
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

    @router.post("/exchange/asset/list")
    async def exchange_list(data: dict, actor: dict = Depends(get_actor_ctx)):
        return exchange.list_asset(actor, data)

    @router.post("/exchange/asset/bid")
    async def exchange_bid(asset_id: str, bid_amount: float, actor: dict = Depends(get_actor_ctx)):
        return exchange.place_bid(actor, asset_id, bid_amount)

    @router.post("/exchange/asset/finalize")
    async def exchange_finalize(asset_id: str, winning_bid_id: str, actor: dict = Depends(get_actor_ctx)):
        return exchange.finalize_exchange(actor, asset_id, winning_bid_id)

    @router.post("/exchange/transfer")
    async def transfer_exchange(data: dict, actor: dict = Depends(get_actor_ctx)):
        return exchange.transfer_asset(actor, data)

    @router.post("/education/enroll")
    async def enroll_education(data: dict, actor: dict = Depends(get_actor_ctx)):
        return education.enroll(actor, data)

    return router
