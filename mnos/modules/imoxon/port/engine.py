class PortEngine:
    def __init__(self, guard, events):
        self.guard = guard
        self.events = events

    def release_clearance(self, actor_ctx: dict, manifest_id: str):
        return self.guard.execute_sovereign_action(
            "imoxon.port.release",
            actor_ctx,
            self._internal_release,
            manifest_id
        )

    def _internal_release(self, manifest_id):
        entry = {"manifest": manifest_id, "status": "RELEASED"}
        self.events.publish("PORT_CLEARANCE_RELEASED", entry)
        return entry
