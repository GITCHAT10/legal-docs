import asyncio
from decimal import Decimal
from pydantic import BaseModel
from typing import Dict, Any, Optional

class EmailEvent(BaseModel):
    trace_id: str
    recipient: str
    segment: str
    trigger: str
    base_amount: Decimal
    product_type: str
    scores: Dict[str, float]

class AsyncEmailQueue:
    def __init__(self):
        self.queue = []

    async def enqueue(self, event: EmailEvent):
        self.queue.append(event)
        # In prod: push to Redis/RabbitMQ
        return True

from ..engine.router import SupplyResponse

class SupplyEXMAILBridge:
    def __init__(self, exmail_queue: AsyncEmailQueue):
        self.queue = exmail_queue

    async def on_inventory_event(self, trace_id: str, response: SupplyResponse):
        if response.trigger_hint == "urgency" and response.availability_pct < 15:
            await self.queue.enqueue(EmailEvent(
                trace_id=f"{trace_id}_urgency",
                recipient="agent_pool@dmcs.mv",
                segment="B2B",
                trigger="low_allotment",
                base_amount=response.net_amount,
                product_type=response.product_type,
                scores={"conversion_score": 0.88, "margin_risk": 0.10}
            ))
        elif response.trigger_hint == "volume" and response.availability_pct > 65:
            await self.queue.enqueue(EmailEvent(
                trace_id=f"{trace_id}_volume",
                recipient="guest_leads@prestige.mv",
                segment="GCC",
                trigger="early_bird_release",
                base_amount=response.net_amount * Decimal("0.90"),
                product_type=response.product_type,
                scores={"conversion_score": 0.76, "margin_risk": 0.18}
            ))
