class TailorGridEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def capture_measurement(self, actor_ctx: dict, staff_id: str, profile: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.tailor.measurement",
            actor_ctx,
            self._internal_capture,
            staff_id, profile
        )

    def _internal_capture(self, staff_id, profile):
        entry = {
            "staff_id": staff_id,
            "profile": profile,
            "status": "MEASURED"
        }
        self.events.publish("TAILOR_MEASUREMENT_CAPTURED", entry)
        return entry
