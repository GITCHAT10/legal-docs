class UTBridge:
    def __init__(self, guard, shadow, events):
        self.guard = guard
        self.shadow = shadow
        self.events = events

    def assign_vessel(self, actor_ctx: dict, manifest_id: str, vessel_id: str):
        return self.guard.execute_sovereign_action(
            "imoxon.ut.assign",
            actor_ctx,
            self._internal_assign,
            manifest_id, vessel_id
        )

    def _internal_assign(self, manifest_id, vessel_id):
        entry = {"manifest": manifest_id, "vessel": vessel_id, "status": "ASSIGNED"}
        self.events.publish("VESSEL_ASSIGNED", entry)
        return entry
