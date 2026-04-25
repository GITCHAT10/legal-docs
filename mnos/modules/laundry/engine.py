import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from decimal import Decimal

class MaldivesLaundryEngine:
    """
    MALDIVES-LAUNDRY-ENGINE: Adopting Ultrawash Multi-Store Model.
    Features: Service Categories (Wash, Dry Clean, Ironing), Multi-Store Registry,
    Pickup/Delivery Integration, and CloudBrain Orchestration.
    Compliance: Maldives Tax Logic (10% SC + 8% GST for services).
    """
    def __init__(self, core, nexus_brain):
        self.core = core
        self.nexus = nexus_brain
        self.stores = {} # store_id -> data
        self.orders = {} # order_id -> data
        self.service_catalog = {
            "WASH_FOLD": {"name": "Wash & Fold", "base_price_mvr": 50.0},
            "DRY_CLEAN": {"name": "Dry Cleaning", "base_price_mvr": 150.0},
            "IRON_ONLY": {"name": "Ironing Only", "base_price_mvr": 30.0}
        }

    def register_laundry_store(self, actor_ctx: dict, store_data: dict):
        """Island GM or Owner action: Register a laundry facility."""
        return self.core.execute_commerce_action(
            "laundry.store.register", actor_ctx, self._internal_register_store, store_data
        )

    def _internal_register_store(self, data):
        store_id = f"LND-{uuid.uuid4().hex[:6].upper()}"
        store = {
            "id": store_id,
            "name": data.get("name"),
            "island": data.get("island"),
            "owner_id": data.get("owner_id"),
            "status": "ACTIVE"
        }
        self.stores[store_id] = store
        return store

    def create_laundry_order(self, actor_ctx: dict, store_id: str, items: List[dict]):
        """Guest or Agent action: Book laundry service."""
        return self.core.execute_commerce_action(
            "laundry.order.create", actor_ctx, self._internal_create_order, store_id, items, actor_ctx
        )

    def _internal_create_order(self, store_id, items, actor_ctx):
        if store_id not in self.stores:
            raise ValueError("Laundry store not found")

        # 1. Calculate Base Total (MVR)
        base_total = Decimal("0")
        for item in items:
            svc_type = item.get("service_type")
            qty = item.get("qty", 1)
            if svc_type in self.service_catalog:
                base_total += Decimal(str(self.service_catalog[svc_type]["base_price_mvr"])) * Decimal(str(qty))

        # 2. Apply Maldives Tax Logic (RETAIL category for services)
        pricing = self.core.fce.calculate_local_order(base_total, "RETAIL")

        order_id = f"ORD-LND-{uuid.uuid4().hex[:6].upper()}"
        order = {
            "id": order_id,
            "store_id": store_id,
            "customer_id": actor_ctx["identity_id"],
            "island": self.stores[store_id]["island"],
            "items": items,
            "pricing": pricing,
            "status": "PICKUP_PENDING",
            "timestamp": datetime.now(UTC).isoformat()
        }

        self.orders[order_id] = order

        # 3. Integrate with Cloud Brain for SHADOW and Settlement
        self.nexus.core.shadow.commit("laundry.order.placed", order_id, order)

        # Simulated Payout Split (4% MARS, 2% NGO)
        self.nexus._calculate_settlement(order_id, float(base_total), pricing, store_id)

        return order

    def update_order_status(self, actor_ctx: dict, order_id: str, status: str):
        """Execution action: Update laundry status (WASHING, READY, DELIVERED)."""
        return self.core.execute_commerce_action(
            "laundry.order.update", actor_ctx, self._internal_update_status, order_id, status
        )

    def _internal_update_status(self, order_id, status):
        if order_id in self.orders:
            self.orders[order_id]["status"] = status
            if status == "DELIVERED":
                # Trigger payout release via Cloud Brain
                self.nexus.finalize_cycle(None, order_id) # Using internal call
            return self.orders[order_id]
        return None
