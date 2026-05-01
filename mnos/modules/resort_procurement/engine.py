import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

class UResortProcurementEngine:
    """
    U-Resort Procurement: Resort-first procurement and vendor quote workflow.
    """
    def __init__(self, upos_core, fce, shadow, logistics):
        self.upos = upos_core
        self.fce = fce
        self.shadow = shadow
        self.logistics = logistics
        self.requests = {}
        self.quotes = {}

    def create_request(self, actor_ctx: dict, data: dict):
        # HARD GATE: Requestor identity
        if not actor_ctx.get("identity_id"):
             raise PermissionError("HARD GATE: No procurement request without AEGIS requestor.")

        r_id = f"PR-{uuid.uuid4().hex[:8].upper()}"
        request = {
            "id": r_id,
            "resort_id": data.get("resort_id"),
            "department": data.get("department"),
            "status": "SUBMITTED",
            "items": data.get("items", []),
            "requested_arrival": data.get("requested_arrival"),
            "budget_reserved": False,
            "created_at": datetime.now(UTC).isoformat()
        }
        self.requests[r_id] = request
        self.shadow.commit("resort_procurement.request.created", actor_ctx["identity_id"], request)
        return request

    def submit_vendor_quote(self, actor_ctx: dict, request_id: str, quote_data: dict):
        # HARD GATE: Verified vendor
        if actor_ctx.get("role") != "vendor":
             raise PermissionError("HARD GATE: No vendor quote without verified vendor.")

        q_id = f"QTE-{uuid.uuid4().hex[:6].upper()}"
        quote = {
            "id": q_id,
            "request_id": request_id,
            "vendor_id": actor_ctx["identity_id"],
            "total": quote_data.get("total"),
            "status": "SUBMITTED",
            "cold_chain": quote_data.get("cold_chain", False)
        }
        self.quotes[q_id] = quote
        self.shadow.commit("resort_procurement.quote.submitted", actor_ctx["identity_id"], quote)
        return quote

    def approve_and_reserve(self, actor_ctx: dict, request_id: str, quote_id: str):
        # Finance approval and FCE budget reserve
        request = self.requests.get(request_id)
        quote = self.quotes.get(quote_id)

        # Simulated FCE check
        request["status"] = "APPROVED"
        request["budget_reserved"] = True
        quote["status"] = "ACCEPTED"

        self.shadow.commit("resort_procurement.budget.reserved", actor_ctx["identity_id"], {"request_id": request_id})
        self.shadow.commit("resort_procurement.quote.accepted", actor_ctx["identity_id"], {"quote_id": quote_id})

        # Trigger logistics manifest
        return {"status": "APPROVED_FOR_LOGISTICS", "request_id": request_id, "quote_id": quote_id}

    def create_recurring_template(self, actor_ctx: dict, data: dict):
        t_id = f"REC-{uuid.uuid4().hex[:6].upper()}"
        template = {
            "id": t_id,
            "resort_id": data.get("resort_id"),
            "department": data.get("department"),
            "items": data.get("items"),
            "frequency": data.get("frequency", "weekly"),
            "status": "ACTIVE"
        }
        self.shadow.commit("recurring_order.template.created", actor_ctx["identity_id"], template)
        return template

    def receive_goods(self, actor_ctx: dict, request_id: str, data: dict):
        request = self.requests.get(request_id)
        request["status"] = "RECEIVED_AT_RESORT"

        receiving_log = {
            "received_by": actor_ctx["identity_id"],
            "quantity": data.get("quantity"),
            "condition": data.get("condition"),
            "temperature_proof": data.get("temperature_proof")
        }

        self.shadow.commit("resort_procurement.delivery.received", actor_ctx["identity_id"], receiving_log)

        # Release final payout via FCE (simulated)
        self.shadow.commit("resort_procurement.final_payout.released", "SYSTEM", {"request_id": request_id})
        return {"status": "COMPLETED", "request_id": request_id}
