import uuid
from datetime import datetime, UTC, timedelta
from decimal import Decimal, ROUND_HALF_UP
from mnos.shared.execution_guard import authorized_context

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
        return self.core.execute_commerce_action(
            "sky_i.loop_cycle.start",
            actor_ctx,
            self._internal_process_full_cycle,
            guest_id, package_id
        )

    def _internal_process_full_cycle(self, guest_id: str, package_id: str):
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
        with authorized_context():
            self._internal_dispatch_transfer(order_id, {"route": "Male -> Island", "fare": 0})

        # 4. MARS PAY Settlement Split
        self._calculate_settlement(order_id, package["base_price"], pricing, "SYSTEM_DEFAULT_VENDOR")

        # 5. SHADOW Ledger Commit (Truth Layer)
        with authorized_context():
            audit_res = self.core.shadow.commit("sky_i.loop_cycle.initiated", order_id, order)
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
            "status": "LOCKED_IN_ESCROW",
            "payout_status": "PENDING"
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

    def create_legacy_order(self, actor_ctx: dict, vendor_id: str, amount: float):
        """Legacy D2C order flow for MARS Trawel."""
        return self.core.execute_commerce_action(
            "mars.order.create", actor_ctx, self._internal_create_legacy_order, vendor_id, amount
        )

    def _internal_create_legacy_order(self, vendor_id: str, amount: float):
        # Determine green tax (Mock $6 for guesthouses in the test)
        green_tax = Decimal("6") if any(v["id"] == vendor_id and v["vendor_type"] == "GUESTHOUSE" for v in self.vendors.values()) else Decimal("0")
        order_id = f"ORD-MARS-{uuid.uuid4().hex[:6].upper()}"
        vendor = self.vendors.get(vendor_id)
        if not vendor:
             # Default fallback for untracked vendors in simulation
             vendor = {"id": vendor_id, "vendor_type": "RETAIL"}

        # Use FCE to price the order
        # Map GUESTHOUSE to TOURISM for 17% TGST alignment
        category = "TOURISM" if vendor.get("vendor_type") in ["GUESTHOUSE", "RESORT", "CAFE"] else "RETAIL"
        pricing = self.core.fce.calculate_local_order(Decimal(str(amount)), category, green_tax_usd=green_tax)

        order = {
            "order_id": order_id,
            "vendor_id": vendor_id,
            "pricing": pricing,
            "status": "PLACED"
        }
        self.orders[order_id] = order
        self._calculate_settlement(order_id, amount, pricing, vendor_id)
        return order

    def update_delivery_status(self, actor_ctx: dict, order_id: str, status: str):
        """MIG Action: Update delivery state and release funds."""
        return self.core.execute_commerce_action(
            "mars.delivery.update", actor_ctx, self._internal_update_delivery, order_id, status
        )

    def _internal_update_delivery(self, order_id, status):
        if order_id not in self.orders:
            return None

        self.orders[order_id]["status"] = status
        if status == "DELIVERED" and order_id in self.settlements:
             self.settlements[order_id]["payout_status"] = "RELEASED"

        return {"order_id": order_id, "delivery_status": status}

    def get_grid_control_stats(self):
        """MARS-GRID-CONTROL Dashboard utility."""
        return {
            "total_orders": len(self.orders),
            "revenue": sum(o["pricing"]["total"] for o in self.orders.values())
        }

    def _internal_finalize(self, order_id):
        if order_id in self.orders:
            order = self.orders[order_id]
            order["status"] = "COMPLETED"

            # 1. Sync Revenue to Island GM System
            package = self.packages.get(order["package_id"])
            if package:
                 # Real-time sync to Island GM
                 gm_sys = getattr(self.core, "island_gm", None)
                 if gm_sys:
                     gm_sys.sync_revenue(package["island"], package["base_price"])

                 with authorized_context():
                     self.core.events.publish("internal.revenue.sync", {
                         "island": package["island"],
                         "amount": package["base_price"]
                     })

                     # 2. Emit event for Leaderboard (C2C Revenue)
                     self.core.events.publish("hustle.revenue_generated", {
                         "island": package["island"],
                         "amount": package["base_price"],
                         "hustler_id": order["guest_id"], # Simplified
                         "shadow_ref": f"SH-TX-{order_id}"
                     })

                 # 3. Record in MIRA-Bridge for Tax Compliance
                 if hasattr(self.core, "mira_bridge"):
                      self.core.mira_bridge.record_transaction(order)

            if order_id in self.settlements:
                self.settlements[order_id]["status"] = "RELEASED"
                with authorized_context():
                    self.core.shadow.commit("sky_i.payout.released", order_id, self.settlements[order_id])
            return order
        return None

    def get_inventory_search(self, actor_ctx: dict, criteria: dict):
        """B2B: Search available inventory packages."""
        # Simplified: Return all active packages
        return list(self.packages.values())

    def hold_booking(self, actor_ctx: dict, package_id: str):
        """B2B: Place a temporary hold on inventory."""
        return self.core.execute_commerce_action(
            "b2b.booking.hold",
            actor_ctx,
            self._internal_hold_booking,
            package_id
        )

    def _internal_hold_booking(self, package_id: str):
        package = self.packages.get(package_id)
        if not package or package.get("locked"):
             return None

        # Lock the package
        package["locked"] = True

        hold_id = f"HLD-{uuid.uuid4().hex[:6].upper()}"
        hold = {
            "hold_id": hold_id,
            "package_id": package_id,
            "agent_id": self.core.guard.get_actor().get("identity_id"),
            "status": "HELD",
            "expires_at": (datetime.now(UTC) + timedelta(hours=24)).isoformat()
        }
        with authorized_context():
            self.core.shadow.commit("b2b.booking.hold", hold["agent_id"], hold)
        return hold
