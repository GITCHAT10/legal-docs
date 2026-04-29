import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List

class MarketplaceEngine:
    """
    Marketplace Order Routing & Sync Layer.
    Consumes verified POS data and orchestrates FCE/UT.
    """
    def __init__(self, wallet, shadow, events):
        self.wallet = wallet
        self.shadow = shadow
        self.events = events
        self.catalog = {} # merchant_id -> {sku -> data}

    def place_marketplace_order(self, customer_id: str, merchant_id: str, items: List[Dict], amount: float, trace_id: str) -> Dict:
        # 1. Place FCE Hold (Escrow simulation)
        hold_ref = f"HOLD-{uuid.uuid4().hex[:8].upper()}"

        order = {
            "order_id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "merchant_id": merchant_id,
            "items": items,
            "total_mvr": amount,
            "status": "payment_held",
            "fce_hold_ref": hold_ref,
            "timestamp": datetime.now(UTC).isoformat()
        }

        # 2. Shadow Audit
        self.shadow.commit("marketplace.order.held", customer_id, order, trace_id=trace_id)

        # 3. Broadcast to Merchant
        self.events.publish("marketplace.order.received", order)

        return order

    def sync_inventory(self, event: Dict[str, Any]):
        """
        Processes catalog sync events from UPOS.
        """
        merchant_id = event.get("merchant_id")
        sku = event.get("sku")
        if merchant_id not in self.catalog:
            self.catalog[merchant_id] = {}
        self.catalog[merchant_id][sku] = event
        print(f"[MARKETPLACE] Catalog synced: {merchant_id} - {sku}")
