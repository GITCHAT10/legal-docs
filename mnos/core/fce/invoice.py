from decimal import Decimal, ROUND_HALF_UP
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List

class FceInvoiceEngine:
    """
    FCE-INVOICE™: Sovereign Billing & Tax Enforcement.
    Implements MIRA 2026 Rules: SC 10%, TGST 17%, Green Tax $6.
    """
    def __init__(self, fce_core, shadow, events):
        self.fce = fce_core
        self.shadow = shadow
        self.events = events
        self.verified_deliveries = set() # manifest_id or event_id

    def register_delivery_event(self, event_id: str, status: str = "PENDING"):
        if status == "VERIFIED":
            self.verified_deliveries.add(event_id)

    def generate_sovereign_invoice(self, actor_ctx: dict, delivery_data: dict, document_hash: str = None) -> Dict[str, Any]:
        """
        NO EVENT -> NO INVOICE rule enforcement.
        EVENT -> VERIFIED -> FCE
        """
        if not document_hash:
            raise PermissionError("FAIL CLOSED: SIG.DOC hash mandatory for sovereign invoice")

        delivery_id = delivery_data.get("delivery_id")
        if delivery_id not in self.verified_deliveries:
            raise PermissionError(f"FAIL CLOSED: No verified delivery event for ID {delivery_id}")

        # 1. Pricing Logic (MIRA 2026)
        base_amount = Decimal(str(delivery_data.get("total_base", 0)))
        category = delivery_data.get("category", "RESORT_SUPPLY")

        # Use FCE Core for standard calculation
        calculation = self.fce.calculate_local_order(base_amount, category)

        invoice = {
            "invoice_id": f"INV-{uuid.uuid4().hex[:8].upper()}",
            "delivery_id": delivery_id,
            "document_hash": document_hash,
            "timestamp": datetime.now(UTC).isoformat(),
            "pricing": calculation,
            "status": "SEALED",
            "currency": "MVR"
        }

        # 2. SHADOW Commit
        self.shadow.commit("fce.invoice.generated", actor_ctx["identity_id"], invoice)

        # 3. Publish Event
        self.events.publish("invoice.generated", invoice)

        return invoice
