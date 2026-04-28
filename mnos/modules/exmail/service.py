import uuid
from datetime import datetime, UTC
from enum import Enum

class TrafficLight(str, Enum):
    AUTO_SEND = "AUTO_SEND"
    DRAFT_ONLY = "DRAFT_ONLY"
    LOCKED = "LOCKED"

class ExMailService:
    """
    ExMail Core Communication Service: Handles sovereign messaging delivery.
    """
    def __init__(self, core):
        self.core = core
        self.messages = {}

    def ingest_message(self, actor_ctx: dict, message_data: dict):
        return self.core.execute_commerce_action(
            "exmail.message.ingest",
            actor_ctx,
            self._internal_ingest,
            message_data
        )

    def _internal_ingest(self, data):
        msg_id = f"MSG-{uuid.uuid4().hex[:6].upper()}"
        message = {
            "id": msg_id,
            "recipient": data.get("recipient"),
            "content": data.get("content"),
            "status": TrafficLight.AUTO_SEND.value,
            "created_at": datetime.now(UTC).isoformat()
        }
        self.messages[msg_id] = message
        return message

    def dispatch_message(self, actor_ctx: dict, msg_id: str):
        return self.core.execute_commerce_action(
            "exmail.message.dispatch",
            actor_ctx,
            self._internal_dispatch,
            msg_id
        )

    def _internal_dispatch(self, msg_id: str):
        msg = self.messages.get(msg_id)
        if not msg: raise ValueError("Message not found")
        msg["dispatched_at"] = datetime.now(UTC).isoformat()
        msg["delivery_status"] = "SENT"
        return msg
