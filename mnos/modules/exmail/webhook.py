from fastapi import APIRouter, Request, Header, HTTPException, Depends
from .service import ExMailService
from typing import Optional

def create_exmail_router(service: ExMailService, get_actor_ctx):
    router = APIRouter(prefix="/exmail", tags=["exmail"])

    @router.post("/webhook/mailchimp")
    async def mailchimp_webhook(request: Request, x_mailchimp_signature: Optional[str] = Header(None)):
        body = await request.body()
        # In production, validate signature
        # if not service.adapter.validate_webhook(x_mailchimp_signature, body):
        #    raise HTTPException(status_code=401, detail="Invalid webhook signature")

        data = await request.json()
        return service.process_webhook_event(data)

    @router.get("/stats")
    async def get_stats(actor: dict = Depends(get_actor_ctx)):
        return service.get_stats()

    @router.post("/campaign/send")
    async def send_campaign(name: str, recipients: list, actor: dict = Depends(get_actor_ctx)):
        return service.send_campaign(actor, name, recipients)

    return router
