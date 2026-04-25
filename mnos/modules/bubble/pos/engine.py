import uuid
from datetime import datetime, UTC
from typing import Dict, Any

class BubblePOSEngine:
    """
    BUBBLE POS Engine (BPE)
    Internal Module — BUBBLE Commerce Layer
    Rebranded & Native Execution Layer for billing, inventory, and merchant operations.
    """
    def __init__(self, core_mnos):
        self.mnos = core_mnos # Authority (Finance, Shadow, Events)
        self.tenants = {} # merchant_id -> inventory

    def create_invoice(self, merchant_id: str, order_data: dict) -> dict:
        """
        Billing execution and invoice generation.
        """
        # compliance via MNOS FCE
        pricing = self.mnos.fce.finalize_invoice(order_data.get("amount"), "RETAIL")

        invoice = {
            "invoice_id": f"BPE-INV-{uuid.uuid4().hex[:8].upper()}",
            "merchant_id": merchant_id,
            "order_id": order_data.get("order_id"),
            "pricing": pricing,
            "status": "ISSUED",
            "timestamp": datetime.now(UTC).isoformat()
        }

        # Audit record
        self.mnos.shadow.commit("bpe.invoice.issued", merchant_id, invoice)
        return invoice

    def update_inventory(self, merchant_id: str, item_id: str, quantity: float, action: str = "DEDUCT") -> dict:
        """
        Warehouse stock control and inventory updates.
        """
        if merchant_id not in self.tenants:
            self.tenants[merchant_id] = {}

        current = self.tenants[merchant_id].get(item_id, 0.0)
        if action == "DEDUCT":
            new_qty = current - quantity
        else:
            new_qty = current + quantity

        self.tenants[merchant_id][item_id] = new_qty

        update = {
            "merchant_id": merchant_id,
            "item_id": item_id,
            "quantity": quantity,
            "new_balance": new_qty,
            "action": action
        }

        self.mnos.events.publish("bpe.inventory.updated", update)
        return update

    def get_stock_level(self, merchant_id: str, item_id: str) -> float:
        return self.tenants.get(merchant_id, {}).get(item_id, 0.0)
