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

    @router.post("/exchange/transfer")
    async def transfer_exchange(data: dict, actor: dict = Depends(get_actor_ctx)):
        return exchange.transfer_asset(actor, data)

    # --- MARS Academy Endpoints ---
    @router.post("/education/courses/create")
    async def create_course(data: dict, actor: dict = Depends(get_actor_ctx)):
        return education.create_course(actor, data)

    @router.get("/education/courses")
    async def list_courses():
        return education.get_courses()

    @router.post("/education/enroll")
    async def enroll_education(data: dict, actor: dict = Depends(get_actor_ctx)):
        return education.enroll(actor, data)

    @router.post("/education/assessment/submit")
    async def submit_assessment(data: dict, actor: dict = Depends(get_actor_ctx)):
        return education.submit_assessment(actor, data)

    @router.get("/education/certificates/verify")
    async def verify_certificate(cert_id: str):
        return education.verify_certificate(cert_id)

    return router
