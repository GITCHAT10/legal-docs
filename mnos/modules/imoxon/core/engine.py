import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

class ImoxonCore:
    """
    Unified iMOXON Core: Governs all commerce actions.
    Rule: AEGIS -> iMOXON CORE -> FCE -> EVENTS -> SHADOW
    """
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def execute(self, action_type: str, actor_ctx: Dict, logic_func: Any, *args, **kwargs):
        """Wraps logic in ExecutionGuard with FCE and Shadow locks."""
        return self.guard.execute_sovereign_action(
            action_type,
            actor_ctx,
            logic_func,
            *args, **kwargs
        )

class SupplierManager:
    def __init__(self, core):
        self.core = core
        self.suppliers = {} # supplier_id -> data

    def connect_supplier(self, actor_ctx: Dict, supplier_data: Dict):
        return self.core.execute(
            "imoxon.supplier.connect",
            actor_ctx,
            self._internal_connect,
            supplier_data
        )

    def _internal_connect(self, data):
        sid = str(uuid.uuid4())
        supplier = {
            "id": sid,
            "name": data.get("name"),
            "type": data.get("type"), # GLOBAL, LOCAL
            "kyc_status": "PENDING",
            "connected_at": datetime.now(UTC).isoformat()
        }
        self.suppliers[sid] = supplier
        self.core.events.publish("imoxon.supplier_connected", supplier)
        return supplier

class CatalogManager:
    def __init__(self, core):
        self.core = core
        self.raw_products = []
        self.catalog = {} # product_id -> data
        self.approval_queue = []

    def import_products(self, actor_ctx: Dict, supplier_id: str, products: List[Dict]):
        return self.core.execute(
            "imoxon.product.import",
            actor_ctx,
            self._internal_import,
            supplier_id, products
        )

    def _internal_import(self, sid, products):
        batch_id = str(uuid.uuid4())
        normalized = []
        for p in products:
            # Normalize
            np = {
                "id": f"p_{uuid.uuid4().hex[:6]}",
                "supplier_id": sid,
                "name": p.get("name"),
                "base_price": p.get("price"),
                "status": "PENDING_APPROVAL"
            }
            normalized.append(np)
            self.approval_queue.append(np)

        self.core.events.publish("imoxon.products_imported", {"batch": batch_id, "count": len(normalized)})
        return {"batch_id": batch_id, "products": normalized}

    def approve_product(self, actor_ctx: Dict, product_id: str):
        return self.core.execute(
            "imoxon.product.approve",
            actor_ctx,
            self._internal_approve,
            product_id
        )

    def _internal_approve(self, pid):
        for p in self.approval_queue:
            if p["id"] == pid:
                p["status"] = "APPROVED"
                self.catalog[pid] = p
                self.core.events.publish("imoxon.product_approved", p)
                return p
        raise ValueError("Product not found in queue")

class PricingEngine:
    def __init__(self, core):
        self.core = core

    def calculate_landed_cost(self, actor_ctx: Dict, base_price: float, category: str):
        return self.core.execute(
            "imoxon.pricing.landed_cost",
            actor_ctx,
            self._internal_calc,
            base_price, category
        )

    def _internal_calc(self, base, cat):
        # 1. Base + 15% Shipping/Customs
        shipping = base * 0.10
        customs = base * 0.05
        # 2. 10% Markup
        markup = (base + shipping + customs) * 0.10
        landed_base = base + shipping + customs + markup

        # 3. FCE Final Tax (10% SC + 17% TGST for B2B/Resort)
        pricing = self.core.fce.finalize_invoice(landed_base, cat)
        return pricing

class OrderManager:
    def __init__(self, core):
        self.core = core
        self.orders = {}

    def create_order(self, actor_ctx: Dict, order_data: Dict):
        return self.core.execute(
            "imoxon.order.create",
            actor_ctx,
            self._internal_create,
            order_data
        )

    def _internal_create(self, data):
        # atomic validation check
        order_id = f"ord_{uuid.uuid4().hex[:8]}"
        order = {
            "id": order_id,
            "buyer": self.core.guard.get_actor().get("identity_id"),
            "items": data.get("items"),
            "pricing": data.get("pricing"),
            "status": "CREATED"
        }
        self.orders[order_id] = order
        self.core.events.publish("imoxon.order_created", order)
        return order
