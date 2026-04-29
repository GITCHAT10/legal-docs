import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from decimal import Decimal, ROUND_HALF_UP

class IslandGMSystem:
    """
    TRAWEL Island GM System: Distributed Business Network Management.
    Each island is managed by an Island GM who controls inventory, vendors,
    and earns commissions based on performance.
    """
    def __init__(self, core, nexus_skyi):
        self.core = core
        self.nexus = nexus_skyi # Cloud Brain access
        self.island_registry = {} # island_name -> gm_id
        self.island_stats = {} # island_name -> {inventory_count, vendor_count, revenue}

    def register_island(self, actor_ctx: dict, island_data: dict):
        """MIG Central Action: Set up a new island node."""
        return self.core.execute_commerce_action(
            "island.registry.setup", actor_ctx, self._internal_register_island, island_data
        )

    def _internal_register_island(self, data):
        island_name = data.get("name")
        gm_id = data.get("gm_id")
        self.island_registry[island_name] = gm_id
        self.island_stats[island_name] = {
            "inventory_count": 0,
            "vendor_count": 0,
            "revenue": 0.0,
            "commission_rate": 0.05 # Initial 5%
        }
        return {"island": island_name, "gm_id": gm_id, "status": "OPERATIONAL"}

    def onboard_vendor_local(self, actor_ctx: dict, vendor_data: dict):
        """Island GM Action: Onboard a local restaurant/shop."""
        island = vendor_data.get("island")
        # Security: Island-bound check
        if actor_ctx.get("role") == "island_gm" and actor_ctx.get("assigned_island") != island:
             raise PermissionError(f"Access Denied: You are only authorized for {actor_ctx.get('assigned_island')}")

        return self.core.execute_commerce_action(
            "island.vendor.onboard", actor_ctx, self._internal_onboard_vendor, vendor_data
        )

    def _internal_onboard_vendor(self, data):
        # 1. Register in Cloud Brain
        vendor = self.nexus._internal_register_vendor(data)

        # 2. Update local stats (linked to commission)
        island = data.get("island")
        self.island_stats[island]["vendor_count"] += 1

        # 3. Dynamic Commission Scaling: more vendors -> higher rate (cap at 15%)
        count = self.island_stats[island]["vendor_count"]
        new_rate = min(0.05 + (count * 0.01), 0.15)
        self.island_stats[island]["commission_rate"] = new_rate

        return {"vendor_id": vendor["id"], "commission_rate": new_rate}

    def get_gm_dashboard(self, actor_ctx: dict, island_name: str):
        """Island Command Panel: Real-time stats for GM."""
        if actor_ctx.get("role") == "island_gm" and actor_ctx.get("assigned_island") != island_name:
             raise PermissionError("Access Denied: Island Mismatch")

        stats = self.island_stats.get(island_name)
        if not stats:
            return None

        # Calculate expected payout
        projected_payout = Decimal(str(stats["revenue"])) * Decimal(str(stats["commission_rate"]))

        return {
            "island": island_name,
            "vendors": stats["vendor_count"],
            "rooms": stats["inventory_count"],
            "revenue": stats["revenue"],
            "commission_rate": stats["commission_rate"],
            "projected_payout": float(projected_payout)
        }

    def sync_revenue(self, island_name: str, amount: float):
        """Internal: Sync revenue from completed orders to island stats."""
        if island_name in self.island_stats:
            self.island_stats[island_name]["revenue"] += amount
            # Audit in SHADOW
            from mnos.shared.execution_guard import ExecutionGuard
            actor = {"identity_id": "SYSTEM", "device_id": "ISLAND-GM-SYNC", "role": "admin"}
            with ExecutionGuard.authorized_context(actor):
                self.core.shadow.commit("island.revenue.sync", island_name, {"amount": amount}, trace_id=f"TR-GM-SYNC-{island_name}-{datetime.now(UTC).timestamp()}")

            # Trigger Scoring update
            gm_id = self.island_registry.get(island_name)
            if gm_id and hasattr(self, "scoring"):
                 self.scoring.update_hustle_score(gm_id, island_name)
