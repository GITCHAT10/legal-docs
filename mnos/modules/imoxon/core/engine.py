import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

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

from mnos.db.session import SessionLocal
from mnos.modules.imoxon.schemas.models import ImoxonSupplier, ImoxonCatalogProduct, ImoxonOrder, ImoxonWarehouseStock

class MerchantManager:
    def __init__(self, core):
        self.core = core

    def get_vendor_status(self, vendor_id: str) -> str:
        with SessionLocal() as db:
            vendor = db.query(ImoxonSupplier).filter(ImoxonSupplier.id == vendor_id).first()
            return vendor.kyc_status if vendor else "UNKNOWN"

    def approve_vendor(self, actor_ctx: dict, vendor_data: dict):
        return self.core.execute_commerce_action(
            "imoxon.vendor.approve",
            actor_ctx,
            self._internal_approve,
            vendor_data
        )

    def _internal_approve(self, data):
        did = data.get("did")
        with SessionLocal() as db:
            vendor = db.query(ImoxonSupplier).filter(ImoxonSupplier.id == did).first()
            if not vendor:
                vendor = ImoxonSupplier(id=did, name=data.get("business_name"), type="LOCAL", kyc_status="VERIFIED")
                db.add(vendor)
            else:
                vendor.kyc_status = "VERIFIED"
            db.commit()

            vendor_dict = {
                "did": did,
                "business_name": data.get("business_name"),
                "kyc_status": "VERIFIED",
                "approved_at": datetime.now(UTC).isoformat()
            }
            self.core.events.publish("imoxon.vendor_approved", vendor_dict)
            return vendor_dict

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

        with SessionLocal() as db:
            p = ImoxonCatalogProduct(
                id=product_id,
                supplier_id=sid,
                name=raw.get("name"),
                base_price=float(base),
                landed_cost=float(landed_base),
                status="PENDING_APPROVAL"
            )
            db.add(p)
            db.commit()

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
        with SessionLocal() as db:
            p = db.query(ImoxonCatalogProduct).filter(ImoxonCatalogProduct.id == pid).first()
            if p:
                p.status = "APPROVED"
                db.commit()
                res = {
                    "id": p.id,
                    "supplier_id": p.supplier_id,
                    "name": p.name,
                    "landed_base": p.landed_cost,
                    "status": p.status
                }
                self.core.events.publish("imoxon.product_goes_live", res)
                return res
        raise ValueError("Product not in queue")

class ProcurementEngine:
    def __init__(self, core):
        self.core = core

    def create_b2b_request(self, actor_ctx: dict, data: dict):
        return self.core.execute_commerce_action(
            "imoxon.b2b.procurement",
            actor_ctx,
            self._internal_procure,
            data
        )

    def _internal_procure(self, data):
        # FCE Validation of pricing
        pricing = self.core.fce.finalize_invoice(data.get("amount"), "RESORT_SUPPLY")
        order_id = f"PR-{uuid.uuid4().hex[:6].upper()}"
        buyer_id = self.core.guard.get_actor().get("identity_id")

        with SessionLocal() as db:
            order = ImoxonOrder(
                id=order_id,
                buyer_id=buyer_id,
                items=data.get("items"),
                pricing=pricing,
                status="ISSUED"
            )
            db.add(order)
            db.commit()

        request = {
            "id": order_id,
            "buyer": buyer_id,
            "items": data.get("items"),
            "pricing": pricing,
            "status": "ISSUED"
        }
        self.core.events.publish("imoxon.b2b_order_created", request)
        self.core.events.publish("procurement.pr_created", request) # Compatibility
        return request

    def create_order(self, actor_ctx: dict, order_data: dict):
        return self.core.execute_commerce_action(
            "imoxon.order.create",
            actor_ctx,
            self._internal_order,
            order_data
        )

    def _internal_order(self, data):
        pricing = self.core.fce.finalize_invoice(data.get("amount"), "RETAIL")
        order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"
        buyer_id = self.core.guard.get_actor().get("identity_id")

        with SessionLocal() as db:
            db_order = ImoxonOrder(
                id=order_id,
                buyer_id=buyer_id,
                items=data.get("items", []),
                pricing=pricing,
                status="PLACED"
            )
            db.add(db_order)
            db.commit()

        order = {
            "id": order_id,
            "vendor_id": data.get("vendor_id"),
            "buyer_id": buyer_id,
            "pricing": pricing,
            "status": "PLACED"
        }
        self.core.events.publish("imoxon.order_created", order)
        return order

    def create_purchase_request(self, actor_ctx: dict, items: list, amount: float):
        return self.create_order(actor_ctx, {"items": items, "amount": amount})

    def approve_order(self, actor_ctx: dict, order_id: str):
        return self.core.execute_commerce_action("imoxon.order.approve", actor_ctx, self._update_order_status, order_id, "APPROVED")

    def mark_dispatched(self, actor_ctx: dict, order_id: str):
        return self.core.execute_commerce_action("imoxon.order.dispatch", actor_ctx, self._update_order_status, order_id, "DISPATCHED")

    def mark_delivered(self, actor_ctx: dict, order_id: str):
        return self.core.execute_commerce_action("imoxon.order.deliver", actor_ctx, self._update_order_status, order_id, "DELIVERED")

    def finalize_invoice(self, actor_ctx: dict, order_id: str):
        return self.core.execute_commerce_action("imoxon.order.invoice", actor_ctx, self._update_order_status, order_id, "INVOICED")

    def settle_payment(self, actor_ctx: dict, order_id: str):
        return self.core.execute_commerce_action("imoxon.order.settle", actor_ctx, self._update_order_status, order_id, "SETTLED")

    def _update_order_status(self, order_id: str, status: str):
        with SessionLocal() as db:
            order = db.query(ImoxonOrder).filter(ImoxonOrder.id == order_id).first()
            if order:
                order.status = status
                db.commit()
                res = {"id": order.id, "status": order.status, "pricing": order.pricing}
                self.core.events.publish(f"procurement.order.{status.lower()}", res)
                # Map to test expectation names
                if status == "APPROVED": self.core.events.publish("procurement.order_approved", res)
                if status == "INVOICED": self.core.events.publish("procurement.invoiced", res)
                return res
        raise ValueError("Order not found")
