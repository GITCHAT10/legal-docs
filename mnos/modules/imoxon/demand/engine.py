class DemandEngine:
    def __init__(self, guard, shadow, events):
        self.guard = guard
        self.shadow = shadow
        self.events = events

    def capture_signal(self, actor_ctx: dict, resort_id: str, items: list, urgency: str = "NORMAL"):
        return self.guard.execute_sovereign_action(
            "imoxon.demand.capture",
            actor_ctx,
            self._internal_capture,
            resort_id, items, urgency
        )

    def _internal_capture(self, resort_id, items, urgency):
        signal_id = f"dem_{hash(str(items)) % 10000}"
        signal = {
            "id": signal_id,
            "resort_id": resort_id,
            "items": items,
            "urgency": urgency,
            "status": "CAPTURED"
        }
        self.events.publish("DEMAND_SIGNAL_CAPTURED", signal)
        return signal
