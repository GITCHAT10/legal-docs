import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

from mnos.modules.imoxon.pricing.engine import PricingEngine

class ImoxonCore:
    """
    Unified iMOXON Core: Governs B2B + B2C commerce flows.
    Pipeline: AEGIS → iMOXON CORE → FCE → EVENTS → SHADOW
    """
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.pricing = PricingEngine(fce)

    def execute_commerce_action(self, action_type: str, actor_ctx: Dict, logic_func: Any, *args, **kwargs):
        """Final approval gate and atomic execution."""
        return self.guard.execute_sovereign_action(
            action_type,
            actor_ctx,
            logic_func,
            *args, **kwargs
        )

class CampaignManager:
    def __init__(self, core):
        self.core = core
        self.campaigns = {}

    def create_campaign(self, actor_ctx: dict, campaign_data: dict):
        return self.core.execute_commerce_action(
            "imoxon.campaign.create",
            actor_ctx,
            self._internal_create,
            campaign_data
        )

    def _internal_create(self, data):
        code = data.get("code")
        self.campaigns[code] = {
            "code": code,
            "discount": data.get("discount", 0),
            "expiry": data.get("expiry"),
            "created_at": datetime.now(UTC).isoformat()
        }
        self.core.events.publish("imoxon.campaign_created", self.campaigns[code])
        return self.campaigns[code]

class MerchantManager:
    def __init__(self, core):
        self.core = core
        self.vendors = {}

    def get_vendor_status(self, vendor_id: str) -> str:
        vendor = self.vendors.get(vendor_id)
        return vendor.get("kyc_status", "PENDING") if vendor else "UNKNOWN"

    def approve_vendor(self, actor_ctx: dict, vendor_data: dict):
        return self.core.execute_commerce_action(
            "imoxon.vendor.approve",
            actor_ctx,
            self._internal_approve,
            vendor_data
        )

    def _internal_approve(self, data):
        did = data.get("did")
        vendor = {
            "did": did,
            "business_name": data.get("business_name"),
            "kyc_status": "VERIFIED",
            "approved_at": datetime.now(UTC).isoformat()
        }
        self.vendors[did] = vendor
        self.core.events.publish("imoxon.vendor_approved", vendor)
        return vendor

class POSManager:
    def __init__(self, core, bpe):
        self.core = core
        self.bpe = bpe # BUBBLE POS Engine (BPE)

    def sync_stock(self, actor_ctx: dict, stock_data: dict):
        return self.core.execute_commerce_action(
            "bpe.pos.sync",
            actor_ctx,
            self._internal_sync,
            stock_data
        )

    def _internal_sync(self, data):
        vendor_id = self.core.guard.get_actor().get("identity_id")
        item = data.get("item")
        count = data.get("count")

        # Delegate to rebranded BPE
        return self.bpe.update_inventory(vendor_id, item, count, action="SYNC")

class CatalogManager:
    def __init__(self, core):
        self.core = core
        self.products = {} # id -> data
        self.approval_queue = []

    def import_supplier_product(self, actor_ctx: dict, supplier_id: str, raw_product: dict):
        return self.core.execute_commerce_action(
            "imoxon.catalog.import",
            actor_ctx,
            self._internal_import,
            supplier_id, raw_product
        )

    def _internal_import(self, sid, raw):
        # 1. Normalize
        product_id = f"p_{uuid.uuid4().hex[:6]}"
        # 2. Calculate Landed Cost (Base + 15% Logistics + 10% Markup)
        base = raw.get("price", 0)
        landed_base = base * 1.15 * 1.10

        normalized = {
            "id": product_id,
            "supplier_id": sid,
            "name": raw.get("name"),
            "landed_base": landed_base,
            "status": "PENDING_APPROVAL"
        }
        self.approval_queue.append(normalized)
        self.core.events.publish("imoxon.product_imported", normalized)
        return normalized

    def approve_product(self, actor_ctx: dict, product_id: str):
        return self.core.execute_commerce_action(
            "imoxon.catalog.approve",
            actor_ctx,
            self._internal_approve,
            product_id
        )

    def _internal_approve(self, pid):
        for p in self.approval_queue:
            if p["id"] == pid:
                p["status"] = "APPROVED"
                self.products[pid] = p
                self.core.events.publish("imoxon.product_goes_live", p)
                return p
        raise ValueError("Product not in queue")

class ProcurementEngine:
    def __init__(self, core):
        self.core = core
        self.requests = {}

    def create_b2b_request(self, actor_ctx: dict, data: dict):
        return self.core.execute_commerce_action(
            "imoxon.b2b.procurement",
            actor_ctx,
            self._internal_procure,
            data
        )

    def _internal_procure(self, data):
        # 1. Advanced Pricing Engine (Prestige DMC logic)
        # Net -> Margin -> FX -> Waterfall -> FCE Validation
        from decimal import Decimal
        from mnos.modules.imoxon.pricing.engine import ProductType, Channel
        from mnos.modules.finance.fce import TaxType

        amount = data.get("amount")
        if amount is None or float(amount) <= 0:
            raise ValueError("FAIL CLOSED: Valid amount required for procurement")

        trace_id = data.get("trace_id", str(uuid.uuid4()))

        pricing = self.core.pricing.calculate_quote(
            net_amount=Decimal(str(amount)),
            currency=data.get("currency", "USD"),
            product_type=ProductType(data.get("product_type", ProductType.PACKAGE)),
            trace_id=trace_id,
            tax_type=TaxType(data.get("tax_type", TaxType.TOURISM_STANDARD)),
            channel=Channel(data.get("channel", Channel.DIRECT)),
            aegis_ctx=actor_ctx
        )

        request = {
            "id": f"PR-{uuid.uuid4().hex[:6].upper()}",
            "buyer": self.core.guard.get_actor().get("identity_id"),
            "items": data.get("items"),
            "pricing": pricing,
            "status": "ISSUED"
        }
        self.core.events.publish("imoxon.b2b_order_created", request)
        return request

    def create_order(self, actor_ctx: dict, order_data: dict):
        return self.core.execute_commerce_action(
            "imoxon.order.create",
            actor_ctx,
            self._internal_order,
            order_data
        )

    def _internal_order(self, data):
        from decimal import Decimal
        from mnos.modules.imoxon.pricing.engine import ProductType, Channel
        from mnos.modules.finance.fce import TaxType

        amount = data.get("amount")
        if amount is None or float(amount) <= 0:
            raise ValueError("FAIL CLOSED: Valid amount required for order")

        trace_id = data.get("trace_id", str(uuid.uuid4()))

        pricing = self.core.pricing.calculate_quote(
            net_amount=Decimal(str(amount)),
            currency=data.get("currency", "USD"),
            product_type=ProductType(data.get("product_type", ProductType.RETAIL)),
            trace_id=trace_id,
            tax_type=TaxType(data.get("tax_type", TaxType.RETAIL)),
            channel=Channel(data.get("channel", Channel.DIRECT)),
            aegis_ctx=actor_ctx
        )
        order = {
            "id": f"ORD-{uuid.uuid4().hex[:6].upper()}",
            "vendor_id": data.get("vendor_id"),
            "buyer_id": self.core.guard.get_actor().get("identity_id"),
            "pricing": pricing,
            "status": "PLACED"
        }
        self.core.events.publish("imoxon.order_created", order)
        return order
