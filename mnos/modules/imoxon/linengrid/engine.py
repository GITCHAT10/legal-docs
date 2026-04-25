class LinenGridEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def track_wash_cycle(self, actor_ctx: dict, tag_id: str):
        return self.guard.execute_sovereign_action(
            "imoxon.linen.wash",
            actor_ctx,
            self._internal_wash,
            tag_id
        )

    def _internal_wash(self, tag_id):
        entry = {"tag_id": tag_id, "action": "WASH", "status": "COMPLETED"}
        self.events.publish("LINEN_WASH_CYCLE_COMPLETED", entry)
        return entry
