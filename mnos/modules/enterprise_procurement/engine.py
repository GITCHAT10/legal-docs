import uuid
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any, Optional

class UEnterpriseProcurementEngine:
    """
    U-Enterprise Procurement: Factory-direct bulk buying and framework agreements.
    Serves national buyers, STO-type enterprises, resort groups, and gov agencies.
    """
    def __init__(self, upos_core, fce, shadow, orca):
        self.upos = upos_core
        self.fce = fce
        self.shadow = shadow
        self.orca = orca
        self.buyers = {}
        self.suppliers = {}
        self.agreements = {}
        self.price_books = {}
        self.requests = {}

    def execute_enterprise_action(self, action_type: str, actor_ctx: dict, logic_func: Any, *args, **kwargs):
        return self.upos.execute_transaction(action_type, actor_ctx, logic_func, *args, **kwargs)

    # --- REGISTRIES ---

    def register_buyer(self, actor_ctx: dict, data: dict):
        return self.execute_enterprise_action(
            "enterprise_procurement.buyer.registered",
            actor_ctx,
            self._internal_register_buyer,
            data
        )

    def _internal_register_buyer(self, data):
        b_id = f"BUY-{uuid.uuid4().hex[:6].upper()}"
        buyer = {
            "id": b_id,
            "name": data.get("legal_name"),
            "type": data.get("buyer_type"), # STO, GOV, RESORT_GROUP
            "approval_threshold": data.get("approval_threshold", 1000000), # 1M MVR
            "aegis_status": "VERIFIED",
            "active_status": "ACTIVE"
        }
        self.buyers[b_id] = buyer
        self.shadow.commit("enterprise_procurement.buyer.registered", "SYSTEM", buyer)
        return buyer

    def register_supplier(self, actor_ctx: dict, data: dict):
        return self.execute_enterprise_action(
            "enterprise_procurement.supplier.registered",
            actor_ctx,
            self._internal_register_supplier,
            data
        )

    def _internal_register_supplier(self, data):
        s_id = f"SUP-{uuid.uuid4().hex[:6].upper()}"
        supplier = {
            "id": s_id,
            "factory_name": data.get("factory_name"),
            "country": data.get("country"),
            "certifications": data.get("certifications", []),
            "aegis_status": "VERIFIED",
            "active_status": "ACTIVE"
        }
        self.suppliers[s_id] = supplier
        self.shadow.commit("enterprise_procurement.supplier.registered", "SYSTEM", supplier)
        return supplier

    # --- FRAMEWORK AGREEMENTS ---

    def create_framework_agreement(self, actor_ctx: dict, data: dict):
        return self.execute_enterprise_action(
            "enterprise_procurement.framework.approved",
            actor_ctx,
            self._internal_create_agreement,
            data
        )

    def _internal_create_agreement(self, data):
        a_id = f"FRM-{uuid.uuid4().hex[:6].upper()}"
        agreement = {
            "id": a_id,
            "buyer_id": data.get("buyer_id"),
            "supplier_id": data.get("supplier_id"),
            "status": "APPROVED",
            "moq_rules": data.get("moq_rules", {}),
            "fx_rules": {"currency": "USD", "adjustment_threshold": 0.05},
            "start_date": datetime.now(UTC).isoformat(),
            "end_date": (datetime.now(UTC) + timedelta(days=365)).isoformat()
        }
        self.agreements[a_id] = agreement
        self.shadow.commit("enterprise_procurement.framework.approved", "SYSTEM", agreement)
        return agreement

    def add_to_price_book(self, actor_ctx: dict, agreement_id: str, item_data: dict):
        return self.execute_enterprise_action(
            "enterprise_procurement.price_book.created",
            actor_ctx,
            self._internal_add_price,
            agreement_id, item_data
        )

    def _internal_add_price(self, agreement_id, item_data):
        p_id = f"PRB-{uuid.uuid4().hex[:6].upper()}"
        price_entry = {
            "id": p_id,
            "agreement_id": agreement_id,
            "sku": item_data.get("sku"),
            "factory_price": item_data.get("price"),
            "currency": item_data.get("currency", "USD"),
            "moq": item_data.get("moq", 100),
            "effective_date": datetime.now(UTC).isoformat()
        }
        self.price_books[p_id] = price_entry
        self.shadow.commit("enterprise_procurement.price_book.created", "SYSTEM", price_entry)
        return price_entry

    # --- BULK PURCHASE REQUESTS ---

    def create_bulk_request(self, actor_ctx: dict, data: dict):
        return self.execute_enterprise_action(
            "enterprise_procurement.request.created",
            actor_ctx,
            self._internal_create_request,
            data
        )

    def _internal_create_request(self, data):
        agreement = self.agreements.get(data.get("agreement_id"))
        if not agreement or agreement["status"] not in ["ACTIVE", "APPROVED"]:
             raise PermissionError("HARD GATE: No procurement from expired/suspended framework agreement.")

        pr_id = f"EPR-{uuid.uuid4().hex[:8].upper()}"
        request = {
            "id": pr_id,
            "buyer_id": data.get("buyer_id"),
            "agreement_id": data.get("agreement_id"),
            "total_estimated_value": data.get("total_value", 0),
            "items": data.get("items"),
            "status": "SUBMITTED",
            "budget_reserved": False
        }
        self.requests[pr_id] = request
        self.shadow.commit("enterprise_procurement.request.created", "SYSTEM", request)
        return request

    def approve_and_reserve_budget(self, actor_ctx: dict, pr_id: str):
        request = self.requests.get(pr_id)
        buyer = self.buyers.get(request["buyer_id"])

        # High-value threshold check
        if request["total_estimated_value"] > buyer["approval_threshold"]:
             if actor_ctx.get("role") not in ["enterprise_admin", "mac_eos_governance"]:
                  raise PermissionError("HARD GATE: Enterprise Admin or Board approval required for high-value order.")

        return self.execute_enterprise_action(
            "enterprise_procurement.approved",
            actor_ctx,
            self._internal_approve,
            pr_id
        )

    def _internal_approve(self, pr_id):
        request = self.requests.get(pr_id)
        request["budget_reserved"] = True
        request["status"] = "APPROVED"
        self.shadow.commit("enterprise_procurement.budget.reserved", "SYSTEM", {"pr_id": pr_id})
        return request

    def confirm_warehouse_receipt(self, actor_ctx: dict, pr_id: str, data: dict):
        return self.execute_enterprise_action(
            "enterprise_procurement.warehouse.received",
            actor_ctx,
            self._internal_receive,
            pr_id, data
        )

    def _internal_receive(self, pr_id, data):
        request = self.requests.get(pr_id)
        request["status"] = "WAREHOUSE_RECEIVED"

        # Record receiving proof
        self.shadow.commit("enterprise_procurement.warehouse.received", "SYSTEM", {
            "pr_id": pr_id,
            "received_by": "AEGIS_ID", # placeholder
            "quality_status": data.get("quality_status")
        })

        # Release Final Payout
        self.shadow.commit("enterprise_procurement.final_payout.released", "SYSTEM", {"pr_id": pr_id})
        return {"status": "COMPLETED", "pr_id": pr_id}
