from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

def create_mail_router(exmail_engine, get_actor_ctx):
    router = APIRouter(prefix="/mail", tags=["mail"])

    @router.post("/send")
    async def send_mail(to: str, subject: str, body: str, actor: dict = Depends(get_actor_ctx)):
        msg = {"to": to, "subject": subject, "body": body}
        msg_id = exmail_engine.process_outbound_mail(actor, msg)
        return {"msg_id": msg_id, "status": "sent"}

    @router.get("/inbox/sync")
    async def sync_inbox(actor: dict = Depends(get_actor_ctx)):
        # Simulate check with Dovecot wrapper
        return {"status": "synced", "new_messages": 0}

    return router
