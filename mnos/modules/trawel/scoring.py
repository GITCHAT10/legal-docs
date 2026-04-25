import uuid
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal, ROUND_HALF_UP

class AtollCommanderScoringEngine:
    """
    Atoll Commander Scoring Engine: Turns the distributed network into an economic battlefield.
    ATOLL_SCORE = (HUSTLE × 0.4) + (PULSE × 0.3) + (BRIDGE × 0.3)
    """
    def __init__(self, core, island_system):
        self.core = core
        self.island_system = island_system
        self.scores = {} # gm_id -> {hustle, pulse, bridge, total}
        self.gm_stats = {} # gm_id -> stats
        self.vendor_registry = {} # vendor_id -> {gm_id, created_at, tx_count, verified}
        self.bridge_events = []

    def update_hustle_score(self, gm_id: str, island: str):
        """
        HUSTLE_SCORE = (Verified Vendors × 10) + (Transactions × 2) + (Revenue × 0.05)
        """
        stats = self.island_system.island_stats.get(island)
        if not stats: return

        # Filtering for active/verified vendors only
        verified_vendors = [v for v in self.core.nexus.vendors.values()
                           if v["island"] == island and self._is_vendor_qualified(v["id"])]

        vendor_count = len(verified_vendors)
        tx_count = sum(self.vendor_registry.get(v["id"], {}).get("tx_count", 0) for v in verified_vendors)
        revenue = stats["revenue"]

        hustle = (vendor_count * 10) + (tx_count * 2) + (revenue * 0.05)
        self._update_gm_score_component(gm_id, "hustle", hustle)

    def _is_vendor_qualified(self, vendor_id: str) -> bool:
        """Vendor must be AEGIS verified and have >= 5 SHADOW transactions."""
        v_data = self.vendor_registry.get(vendor_id)
        if not v_data: return False

        # In a real system, we'd check AEGIS and SHADOW ledger counts
        return v_data.get("verified", False) and v_data.get("tx_count", 0) >= 5

    def update_pulse_score(self, gm_id: str, baseline: float, current: float):
        """
        PULSE_SCORE = ((Baseline - Current) / Baseline) × 100 × 5
        """
        if baseline <= 0: return
        improvement = (baseline - current) / baseline
        pulse = improvement * 100 * 5
        self._update_gm_score_component(gm_id, "pulse", pulse)

    def record_bridge_event(self, actor_ctx: dict, event: dict):
        """
        BRIDGE_SCORE = (Rerouted Guests × 8) + (Cross-Island Revenue × 0.1) + (Collaboration Bonus)
        """
        origin_island = event.get("origin")
        dest_island = event.get("destination")
        origin_gm = self.island_system.island_registry.get(origin_island)
        dest_gm = self.island_system.island_registry.get(dest_island)

        # 1. Anti-Cheat: Fake Capacity Signal (-100 penalty)
        if event.get("reported_capacity", 0) > 0.9 and event.get("actual_capacity", 0) < 0.8:
            self._apply_penalty(origin_gm, 100, "FAKE_CAPACITY_SIGNAL")
            return {"status": "REJECTED", "reason": "Capacity Fraud Detected"}

        # 2. Anti-Cheat: Self-Routing Fraud (No points)
        if self._check_vendor_ownership_conflict(origin_gm, event.get("vendor_id")):
            return {"status": "REJECTED", "reason": "Self-Routing Conflict"}

        # 3. SHADOW Consistency Check: Ensure payment exists
        if not event.get("shadow_payment_ref"):
             return {"status": "INVALID", "reason": "Missing SHADOW payment trail"}

        # 4. Validation: Origin island > 90% capacity
        if event.get("actual_capacity", 0) < 0.9:
            return {"status": "IGNORED", "reason": "Origin island not at capacity"}

        # 5. Success: Bridge established
        bonus = 0
        if event.get("collaborated"):
            bonus = 50 # Collaboration Bonus
            if event.get("prevented_cancellation"):
                bonus = 100

        # Update scores for both GMs
        points = 8 + bonus + (event.get("revenue", 0) * 0.1)
        self._update_gm_score_component(origin_gm, "bridge", points, incremental=True)
        self._update_gm_score_component(dest_gm, "bridge", points, incremental=True)

        # 6. SHADOW Enforcement
        self.core.shadow.commit("atoll.bridge.event", origin_gm, {
            "origin": origin_island,
            "destination": dest_island,
            "points": float(points),
            "ref": event.get("shadow_payment_ref")
        })

        return {"status": "BRIDGE_SUCCESS", "points_awarded": float(points)}

    def _update_gm_score_component(self, gm_id, component, value, incremental=False):
        if gm_id not in self.scores:
            self.scores[gm_id] = {"hustle": 0.0, "pulse": 0.0, "bridge": 0.0, "total": 0.0}

        if incremental:
            self.scores[gm_id][component] += float(value)
        else:
            self.scores[gm_id][component] = float(value)

        # Recalculate Total
        s = self.scores[gm_id]
        s["total"] = (s["hustle"] * 0.4) + (s["pulse"] * 0.3) + (s["bridge"] * 0.3)

    def _apply_penalty(self, gm_id, amount, reason):
        if gm_id in self.scores:
            self.scores[gm_id]["total"] -= amount
            self.core.shadow.commit("atoll.commander.penalty", gm_id, {"amount": amount, "reason": reason})

    def _check_vendor_ownership_conflict(self, gm_id, vendor_id):
        # Mock check: Does the GM own the target vendor?
        return False # Placeholder

    def get_rankings(self):
        """Top 3 GMs for Reward Triggers."""
        sorted_gms = sorted(self.scores.items(), key=lambda x: x[1]["total"], reverse=True)
        return sorted_gms[:3]
