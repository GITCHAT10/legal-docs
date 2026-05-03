from fastapi import APIRouter, Depends
from decimal import Decimal

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

    @router.post("/exchange/transfer")
    async def transfer_exchange(data: dict, actor: dict = Depends(get_actor_ctx)):
        return exchange.transfer_asset(actor, data)

    @router.post("/education/enroll")
    async def enroll_education(data: dict, actor: dict = Depends(get_actor_ctx)):
        return education.enroll(actor, data)

    @router.post("/pricing/landed-cost")
    async def calculate_landed_cost(base: float, cat: str = "RETAIL", actor: dict = Depends(get_actor_ctx)):
        # Base + 15% Logistics + 10% Markup
        landed_base = base * 1.15 * 1.10
        # Maldives Tax Rules via FCE
        from main import fce_core
        return fce_core.calculate_local_order(Decimal(str(landed_base)), cat)

    return router
