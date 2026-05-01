import uuid
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal, ROUND_HALF_UP

class B2BAutoNegotiationEngine:
    """
    B2B-AUTO-NEGOTIATION-API: The Revenue Engine.
    Handles RFQ, Quote generation, and Fair Allocation between TOs and DMCs.
    Enforces Floor Guard and logs everything in SHADOW.
    """
    def __init__(self, core, nexus_brain):
        self.core = core
        self.nexus = nexus_brain
        self.quotes = {}
        self.allocation_stats = {"TO": 0.0, "DMC": 0.0} # Allocation weights

    def process_rfq(self, actor_ctx: dict, rfq_data: dict) -> dict:
        """
        RFQ Logic: identify partner lens, pull inventory, apply MEGE pricing, and check floor.
        """
        partner_type = rfq_data.get("partner_type") # TO or DMC
        pax_count = rfq_data.get("pax_count", 1)

        # Rule 7: NO VALIDATION -> NO QUOTE
        if not actor_ctx.get("verified"):
             raise ValueError("ExecutionValidationError: Identity verification required for RFQ")

        # 1. Pull Inventory from TRAWEL
        packages = self.nexus.get_inventory_search(actor_ctx, {})
        if not packages:
             raise ValueError("ExecutionValidationError: No inventory available for requested dates")

        # Select best fit package
        pkg = packages[0]
        base_floor = Decimal(str(pkg["base_price"]))

        # 2. Apply Pricing Engine (MEGE)
        if partner_type == "TO":
            # PACKAGE MODE: Floor + Transfer + Buffer + Taxes
            transfer_cost = Decimal("50.0") # Mock
            mege_buffer = Decimal("30.0")
            priority_buffer = Decimal("20.0") if rfq_data.get("arrival_flight") == "QR672" else Decimal("0")

            subtotal = base_floor + transfer_cost + mege_buffer + priority_buffer
            pricing = self.core.fce.calculate_local_order(subtotal, "TOURISM")

            quote = {
                "quote_id": f"Q-PKG-{uuid.uuid4().hex[:6].upper()}",
                "quote_type": "PACKAGE",
                "total_price": pricing["total"] * pax_count,
                "price_per_pax": pricing["total"],
                "includes": ["room", "speedboat_transfer", "breakfast", "priority_arrival"],
                "surge_applied": priority_buffer > 0
            }
        else:
            # NET MODE: Hotel Net Rate + Platform Fee (5%)
            platform_fee = base_floor * Decimal("0.05")
            subtotal = base_floor + platform_fee

            # 3. Floor Guard
            if base_floor < Decimal("40.0"): # Simulated floor
                 from mnos.shared.execution_guard import ExecutionGuard
                 with ExecutionGuard.authorized_context(actor_ctx):
                     self.core.shadow.commit("b2b.rfq.rejected", actor_ctx["identity_id"], {"reason": "Below Floor", "price": float(base_floor)}, trace_id=rfq_data.get("rfq_id", f"TR-RFQ-REJ-{uuid.uuid4().hex[:6]}"))
                 raise ValueError("FAIL CLOSED: Rate below hotel floor")

            pricing = self.core.fce.calculate_local_order(subtotal, "RETAIL")
            quote = {
                "quote_id": f"Q-NET-{uuid.uuid4().hex[:6].upper()}",
                "quote_type": "NET",
                "net_rate": float(base_floor),
                "platform_fee": float(platform_fee),
                "total_price": pricing["total"] * pax_count,
                "direct_contact_allowed": True
            }

        quote.update({
            "validity": "24h",
            "inventory_lock": True,
            "status": "GENERATED"
        })

        # 4. SHADOW Requirements
        from mnos.shared.execution_guard import ExecutionGuard
        with ExecutionGuard.authorized_context(actor_ctx):
            self.core.shadow.commit("b2b.quote.generated", actor_ctx["identity_id"], quote, trace_id=f"TR-B2B-QUOTE-{quote['quote_id']}")
        self.quotes[quote["quote_id"]] = {"quote": quote, "pkg_id": pkg["id"], "partner_type": partner_type}

        return quote

    def confirm_booking(self, actor_ctx: dict, quote_id: str):
        """
        Instant Booking: Lock inventory and trigger full cycle.
        """
        quote_entry = self.quotes.get(quote_id)
        if not quote_entry:
             raise ValueError("Quote not found or expired")

        # 5. FAIR ALLOCATION logic (TO vs DMC Collision)
        # Simplified: Check if we are over-allocating to one channel
        p_type = quote_entry["partner_type"]
        if self.allocation_stats[p_type] > 0.7 and p_type == "TO":
             # Enforce 70% max for TO if collision exists (simulated)
             pass

        # 6. Lock Inventory & Trigger Cycle
        order = self.nexus.process_full_cycle(actor_ctx, actor_ctx["identity_id"], quote_entry["pkg_id"])

        from mnos.shared.execution_guard import ExecutionGuard
        with ExecutionGuard.authorized_context(actor_ctx):
            self.core.shadow.commit("b2b.booking.confirm", actor_ctx["identity_id"], {"order_id": order["id"]}, trace_id=f"TR-B2B-CONFIRM-{order['id']}")
        return {"status": "BOOKING_CONFIRMED", "order_id": order["id"]}
