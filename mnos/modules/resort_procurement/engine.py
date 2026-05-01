import uuid
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any, Optional

class UResortProcurementEngine:
    """
    U-Resort Procurement: Resort-first procurement and vendor quote workflow.
    Supports cold-chain SLA, department-level requests, and recurring orders.
    """
    def __init__(self, upos_core, fce, shadow, logistics):
        self.upos = upos_core
        self.fce = fce
        self.shadow = shadow
        self.logistics = logistics
        self.requests = {}
        self.quotes = {}
        self.recurring_templates = {}

        self.categories = [
            "F&B perishables", "F&B dry goods", "Beverages / bonded stock",
            "Housekeeping amenities", "Linen and laundry", "Cleaning chemicals",
            "Spa supplies", "Marine and dive gear", "Engineering and utilities",
            "Medical clinic supplies", "IT and POS hardware", "Office supplies"
        ]

    def create_request(self, actor_ctx: dict, data: dict):
        if not actor_ctx.get("identity_id"):
             raise PermissionError("HARD GATE: No procurement request without AEGIS requestor.")

        r_id = f"PR-{uuid.uuid4().hex[:8].upper()}"
        request = {
            "id": r_id,
            "resort_id": data.get("resort_id"),
            "department": data.get("department"),
            "requestor_id": actor_ctx["identity_id"],
            "budget_code": data.get("budget_code"),
            "priority": data.get("priority", "NORMAL"),
            "requested_arrival_date": data.get("requested_arrival_date"),
            "requested_arrival_window": data.get("requested_arrival_window"),
            "harbour_location": data.get("harbour_location"),
            "destination_resort_jetty": data.get("destination_resort_jetty"),
            "items": data.get("items", []), # List of line items with categories
            "cold_chain_required": data.get("cold_chain_required", False),
            "status": "SUBMITTED",
            "documents": {"commercial_invoice": "PENDING", "packing_list": "PENDING"},
            "created_at": datetime.now(UTC).isoformat()
        }
        self.requests[r_id] = request
        self.shadow.commit("resort_procurement.request.created", actor_ctx["identity_id"], request)
        return request

    def submit_vendor_quote(self, actor_ctx: dict, request_id: str, quote_data: dict):
        if actor_ctx.get("role") != "vendor":
             raise PermissionError("HARD GATE: No vendor quote without verified vendor.")

        q_id = f"QTE-{uuid.uuid4().hex[:6].upper()}"
        quote = {
            "id": q_id,
            "request_id": request_id,
            "vendor_id": actor_ctx["identity_id"],
            "subtotal": quote_data.get("subtotal"),
            "discount": quote_data.get("discount", 0),
            "tax": quote_data.get("tax", 0),
            "logistics_charge": quote_data.get("logistics_charge", 0),
            "total": quote_data.get("total"),
            "deposit_percent": quote_data.get("deposit_percent", 0),
            "deposit_amount": quote_data.get("deposit_amount", 0),
            "payment_terms": quote_data.get("payment_terms"),
            "status": "SUBMITTED",
            "cold_chain_commitment": quote_data.get("cold_chain", False),
            "sla_terms": {
                "delivery_window": quote_data.get("delivery_window"),
                "temperature_monitoring": quote_data.get("temp_monitoring", False),
                "damage_deduction_pct": 0.10,
                "delay_liability_clause": True
            }
        }
        self.quotes[q_id] = quote
        self.shadow.commit("resort_procurement.quote.submitted", actor_ctx["identity_id"], quote)
        return quote

    def approve_and_reserve(self, actor_ctx: dict, request_id: str, quote_id: str):
        request = self.requests.get(request_id)
        quote = self.quotes.get(quote_id)

        if not request or not quote:
            raise ValueError("Request or Quote not found")

        # Threshold check for GM approval
        if quote["total"] > 50000 and actor_ctx.get("role") not in ["resort_gm", "admin"]:
             raise PermissionError("HARD GATE: GM approval required for orders above 50,000 MVR.")

        request["status"] = "APPROVED"
        request["budget_reserved"] = True
        quote["status"] = "ACCEPTED"

        self.shadow.commit("resort_procurement.budget.reserved", actor_ctx["identity_id"], {"request_id": request_id})
        self.shadow.commit("resort_procurement.quote.accepted", actor_ctx["identity_id"], {"quote_id": quote_id})

        return {"status": "APPROVED_FOR_LOGISTICS", "request_id": request_id, "quote_id": quote_id}

    def upload_procurement_document(self, actor_ctx: dict, request_id: str, doc_type: str, file_hash: str):
        request = self.requests.get(request_id)
        request["documents"][doc_type] = {"hash": file_hash, "status": "UPLOADED"}
        self.shadow.commit("resort_procurement.document.uploaded", actor_ctx["identity_id"], {"request_id": request_id, "type": doc_type})
        return True

    def receive_goods(self, actor_ctx: dict, request_id: str, data: dict):
        request = self.requests.get(request_id)

        # Quality Control: check for required docs before receipt
        if any(status == "PENDING" for status in request["documents"].values()):
             raise PermissionError("HARD GATE: Cannot receive goods without required documents.")

        # Cold Chain Validation Logic
        if request.get("cold_chain_required") and not data.get("temperature_proof"):
             self.shadow.commit("resort_procurement.dispute.opened", actor_ctx["identity_id"], {
                 "request_id": request_id,
                 "reason": "Cold chain temperature proof missing"
             })
             request["status"] = "DISPUTED"
             return {"status": "DISPUTED", "reason": "Cold chain proof required for payout."}

        request["status"] = "RECEIVED_AT_RESORT"
        receiving_log = {
            "received_by": actor_ctx["identity_id"],
            "received_time": datetime.now(UTC).isoformat(),
            "quantity": data.get("quantity"),
            "condition": data.get("condition"),
            "temperature_proof": data.get("temperature_proof"),
            "photo_proof": data.get("photo_url")
        }
        self.shadow.commit("resort_procurement.delivery.received", actor_ctx["identity_id"], receiving_log)
        self.shadow.commit("resort_procurement.final_payout.released", "SYSTEM", {"request_id": request_id})
        return {"status": "COMPLETED", "request_id": request_id}

    def create_recurring_template(self, actor_ctx: dict, data: dict):
        t_id = f"REC-{uuid.uuid4().hex[:6].upper()}"
        template = {
            "id": t_id,
            "resort_id": data.get("resort_id"),
            "department": data.get("department"),
            "items": data.get("items"),
            "frequency": data.get("frequency", "weekly"),
            "max_cycle_budget": data.get("max_budget"),
            "budget_code": data.get("budget_code"),
            "status": "ACTIVE",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.recurring_templates[t_id] = template
        self.shadow.commit("recurring_order.template.created", actor_ctx["identity_id"], template)
        return template
