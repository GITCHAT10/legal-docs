from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI(title="MNOS NOTIFICATIONS")

class Notification(BaseModel):
    recipient_id: str
    message: str
    type: str

@app.post("/api/notifications/send")
async def send_notification(notification: Notification):
    return {"status": "success", "message_id": f"MSG-{uuid.uuid4()}"}

@app.get("/health")
async def health():
    return {"status": "ok"}
