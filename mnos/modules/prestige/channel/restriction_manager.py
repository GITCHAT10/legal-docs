import time
from typing import Dict, Any

class RestrictionManager:
    def __init__(self, core_system):
        self.core = core_system
        self.restrictions: Dict[str, Dict[str, Any]] = {} # item_id -> restrictions

    def set_restriction(self, actor_ctx: dict, item_id: str, restriction_type: str, value: Any):
        return self.core.guard.execute_sovereign_action(
            "prestige.channel.set_restriction",
            actor_ctx,
            self._internal_set,
            item_id, restriction_type, value
        )

    def _internal_set(self, item_id: str, restriction_type: str, value: Any):
        if item_id not in self.restrictions:
            self.restrictions[item_id] = {}

        self.restrictions[item_id][restriction_type] = {
            "value": value,
            "version": self.restrictions[item_id].get(restriction_type, {}).get("version", 0) + 1,
            "updated_at": time.time()
        }

        actor = self.core.guard.get_actor()
        actor_id = actor.get("identity_id") if actor else "SYSTEM"

        self.core.shadow.commit("prestige.restriction.updated", actor_id, {
            "item_id": item_id,
            "restriction_type": restriction_type,
            "value": value,
            "version": self.restrictions[item_id][restriction_type]["version"]
        })
        return {"status": "success", "item_id": item_id, "type": restriction_type}

    def get_restrictions(self, item_id: str) -> Dict[str, Any]:
        return self.restrictions.get(item_id, {})
