import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from decimal import Decimal, ROUND_HALF_UP

class NexusSkyICloudBrain:
    """
    NEXUS SKY-i OS: The Central Cloud Brain of the Maldives Sovereign Stack.
    Orchestrates:
    - TRAWEL (Demand Intelligence & Inventory Brain)
    - UT SYSTEM (Physical Execution & Transport)
    - VENDORS (Real-world assets)
    - SHADOW (Immutable Ledger of Truth)
    - MARS PAY (Money Flow & Splits)
    """
    def __init__(self, core, bpe, transport):
        self.core = core
        self.bpe = bpe # UIP-SYNC-LAYER
        self.ut = transport # UT SYSTEM Execution Layer
        self.owners = {}
        self.vendors = {}
        self.orders = {}
        self.settlements = {}
        self.packages = {} # TRAWEL Packages

    # --- TRAWEL (Demand Brain) ---
    def predict_and_build_package(self, actor_ctx: dict, config: dict):
        """TRAWEL: Predict demand and build inventory packages."""
        return self.core.execute_commerce_action(
            "trawel.package.build", actor_ctx, self._internal_build_package, config
        )

    def _internal_build_package(self, config):
        pkg_id = f"PKG-{uuid.uuid4().hex[:6].upper()}"
        package = {
            "id": pkg_id,
            "name": config.get("name"),
            "island": config.get("island"),
            "inventory": config.get("inventory"),
            "base_price": config.get("base_price"),
            "status": "READY_FOR_ALLOCATION"
        }
        self.packages[pkg_id] = package
        self.core.events.publish("trawel.package_built", package)
        return package

    # --- UT SYSTEM (Execution Layer) ---
    def execute_transfer(self, actor_ctx: dict, order_id: str, transfer_data: dict):
        """UT SYSTEM: Dispatch and execute physical movement."""
        return self.core.execute_commerce_action(
            "ut.transfer.dispatch", actor_ctx, self._internal_dispatch_transfer, order_id, transfer_data
        )

    def _internal_dispatch_transfer(self, order_id, data):
        manifest = self.ut._internal_book(data) # Reuse UT logic
        if order_id in self.orders:
            self.orders[order_id]["transfer_id"] = manifest["ticket_id"]
            self.orders[order_id]["status"] = "TRANSFER_IN_PROGRESS"
        return manifest

    # --- CLOSED LOOP ECONOMY FLOW ---
    def process_full_cycle(self, actor_ctx: dict, guest_id: str, package_id: str):
        """
        Closed-Loop Economy Loop:
        Guest orders -> TRAWEL predicts/assigns -> UT executes -> Vendor fulfills -> MARS PAY splits -> SHADOW records -> Cloud Updates.
        """
        package = self.packages.get(package_id)
        if not package:
            raise ValueError("Invalid Package")

        # 1. TRAWEL Assigns Inventory
        order_id = f"ORD-SKY-{uuid.uuid4().hex[:6].upper()}"

        # 2. FCE Compliance Logic (MIRA Tax Engine)
        pricing = self.core.fce.calculate_local_order(Decimal(str(package["base_price"])), "TOURISM")

        order = {
            "id": order_id,
            "guest_id": guest_id,
            "package_id": package_id,
            "pricing": pricing,
            "status": "INITIATED",
            "audit_id": None
        }
        self.orders[order_id] = order

        # 3. UT SYSTEM Dispatches (Fleet Consolidation)
        transfer_manifest = self._internal_dispatch_transfer(order_id, {"route": "Male -> Island", "fare": 0})

        # 4. MARS PAY Settlement Split
        self._calculate_settlement(order_id, package["base_price"], pricing, "SYSTEM_DEFAULT_VENDOR")

        # 5. SHADOW Ledger Commit (Truth Layer)
        audit_res = self.core.shadow.commit("sky_i.loop_cycle.start", order_id, order)
        order["audit_id"] = audit_res

        self.core.events.publish("sky_i.full_cycle_initiated", order)
        return order

    def _calculate_settlement(self, order_id, base_amount, pricing, vendor_id):
        base = Decimal(str(base_amount))
        # Fixed MARS/NGO Fees
        mars_fee = (base * Decimal("0.04")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        ngo_fee = (base * Decimal("0.02")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        vendor_net = base - mars_fee - ngo_fee

        tax_vault = Decimal(str(pricing["service_charge"])) + Decimal(str(pricing["tax_amount"]))

        settlement = {
            "order_id": order_id,
            "vendor_net": float(vendor_net),
            "mars_fee": float(mars_fee),
            "ngo_fee": float(ngo_fee),
            "tax_vault": float(tax_vault),
            "status": "LOCKED_IN_ESCROW"
        }
        self.settlements[order_id] = settlement
        return settlement

    def register_owner(self, actor_ctx: dict, owner_data: dict):
        return self.core.execute_commerce_action(
            "mars.owner.register", actor_ctx, self._internal_register_owner, owner_data
        )

    def _internal_register_owner(self, data):
        owner_id = f"OWN-{uuid.uuid4().hex[:6].upper()}"
        owner = {
            "id": owner_id,
            "legal_name": data.get("legal_name"),
            "kyc_status": "VERIFIED",
            "mars_wallet_id": f"MW-{uuid.uuid4().hex[:8].upper()}"
        }
        self.owners[owner_id] = owner
        return owner

    def register_vendor(self, actor_ctx: dict, vendor_data: dict):
        return self.core.execute_commerce_action(
            "mars.vendor.register", actor_ctx, self._internal_register_vendor, vendor_data
        )

    def _internal_register_vendor(self, data):
        vendor_id = f"VEN-{uuid.uuid4().hex[:6].upper()}"
        vendor = {
            "id": vendor_id,
            "owner_id": data.get("owner_id"),
            "name": data.get("name"),
            "island": data.get("island"),
            "vendor_type": data.get("vendor_type"), # CAFE, GUESTHOUSE
            "mars_fee_pct": Decimal("0.04"), # 4%
            "ngo_fee_percent": Decimal("0.02")   # 2%
        }
        self.vendors[vendor_id] = vendor
        return vendor

    def finalize_cycle(self, actor_ctx: dict, order_id: str):
        """Final fulfillment and payout release."""
        return self.core.execute_commerce_action(
            "sky_i.loop_cycle.finalize", actor_ctx, self._internal_finalize, order_id
        )

    def _internal_finalize(self, order_id):
        if order_id in self.orders:
            self.orders[order_id]["status"] = "COMPLETED"
            if order_id in self.settlements:
                self.settlements[order_id]["status"] = "RELEASED"
                self.core.shadow.commit("sky_i.payout.released", order_id, self.settlements[order_id])
            return self.orders[order_id]
        return None
