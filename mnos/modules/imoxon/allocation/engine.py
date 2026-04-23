class AllocationEngine:
    def __init__(self, guard, events):
        self.guard = guard
        self.events = events

    def lock_allocation(self, actor_ctx: dict, lot_id: str, resort_id: str):
        return self.guard.execute_sovereign_action(
            "imoxon.allocation.lock",
            actor_ctx,
            self._internal_lock,
            lot_id, resort_id
        )

    def _internal_lock(self, lot_id, resort_id):
        entry = {"lot": lot_id, "resort": resort_id, "status": "LOCKED"}
        self.events.publish("ALLOCATION_LOCKED", entry)
        return entry
