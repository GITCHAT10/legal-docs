import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List

class UPOSEngine:
    """
    UPOS Engine (Unified POS) for SALA Node.
    Handles F&B mode, inventory, and order processing.
    """
    def __init__(self, fce, shadow, events):
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.inventory = {} # item_id -> qty

    def create_order(self, merchant_id: str, actor_id: str, items: List[Dict], amount: float) -> Dict:
        # 1. Price calculation via FCE
        pricing = self.fce.calculate_order(amount, category="RETAIL")

        order = {
            "order_id": f"UPOS-{uuid.uuid4().hex[:8].upper()}",
            "merchant_id": merchant_id,
            "items": items,
            "pricing": pricing,
            "status": "COMPLETED",
            "timestamp": datetime.now(UTC).isoformat()
        }

        # 2. Audit in SHADOW
        self.shadow.commit("upos.order.created", actor_id, order)

        # 3. Publish Event
        self.events.publish("upos.order.completed", order)

        return order

    def update_inventory(self, item_id: str, qty: float):
        self.inventory[item_id] = self.inventory.get(item_id, 0.0) + qty
