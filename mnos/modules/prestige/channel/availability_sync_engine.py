import time
from typing import Dict, Any, List, Optional
from mnos.shared.execution_guard import ExecutionGuard

class AvailabilitySyncEngine:
    def __init__(self, core_system):
        self.core = core_system
        self.canonical_availability: Dict[str, int] = {} # item_id -> count

    def set_availability(self, actor_ctx: dict, item_id: str, count: int):
        return self.core.guard.execute_sovereign_action(
            "prestige.channel.set_availability",
            actor_ctx,
            self._internal_set_availability,
            item_id, count
        )

    def _internal_set_availability(self, item_id: str, count: int):
        if count < 0:
            raise ValueError("Inventory cannot go below zero")

        self.canonical_availability[item_id] = count

        actor = self.core.guard.get_actor()
        actor_id = actor.get("identity_id") if actor else "SYSTEM"

        self.core.shadow.commit("prestige.availability.updated", actor_id, {
            "item_id": item_id,
            "count": count,
            "timestamp": time.time()
        })
        return {"status": "success", "item_id": item_id, "count": count}

    def adjust_availability(self, actor_ctx: dict, item_id: str, delta: int):
        return self.core.guard.execute_sovereign_action(
            "prestige.channel.adjust_availability",
            actor_ctx,
            self._internal_adjust,
            item_id, delta
        )

    def _internal_adjust(self, item_id: str, delta: int):
        current = self.canonical_availability.get(item_id, 0)
        new_count = current + delta
        if new_count < 0:
             raise ValueError("Insufficient inventory")

        self.canonical_availability[item_id] = new_count

        self.core.shadow.commit("prestige.availability.adjusted", "SYSTEM", {
            "item_id": item_id,
            "delta": delta,
            "new_count": new_count
        })
        return {"status": "success", "new_count": new_count}

    def check_stop_sell(self, item_id: str) -> bool:
        item = self.core.inventory_mapper.get_item(item_id)
        if not item: return True

        if item.status == "STOP_SELL": return True
        if not item.cancellation_policy_ref: return True

        # In real system, check transfer feasibility etc.
        return False
