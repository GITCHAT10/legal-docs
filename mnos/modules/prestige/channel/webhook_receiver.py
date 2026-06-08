import time
import json
from typing import Dict

class WebhookReceiver:
    def __init__(self, core_system):
        self.core = core_system
        self.processed_webhooks: set = set() # For idempotency / replay protection

    async def receive_webhook(self, channel_id: str, signature: str, payload: str, headers: Dict[str, str]):
        # 1. Auth Gateway check
        if not self.core.auth_gateway.validate_request(channel_id, signature, payload, headers):
             return {"status": "error", "message": "Unauthorized"}

        data = json.loads(payload)
        webhook_id = data.get("webhook_id")

        # 2. Replay / Idempotency check
        if webhook_id in self.processed_webhooks:
            return {"status": "success", "message": "Already processed"}

        self.processed_webhooks.add(webhook_id)

        # 3. Seal Intake to SHADOW
        self.core.shadow.commit("prestige.channel.webhook_intake", "SYSTEM", {
            "channel_id": channel_id,
            "webhook_id": webhook_id,
            "timestamp": time.time()
        })

        # 4. Routing
        event_type = data.get("event_type")
        if event_type == "RESERVATION_UPDATE":
             # Process update
             pass
        elif event_type == "CANCELLATION":
             # Process cancellation
             pass

        # 5. Emit Event
        if hasattr(self.core, "events"):
            self.core.events.emit(f"prestige.channel.webhook.{event_type}", data)

        return {"status": "success", "webhook_id": webhook_id}
