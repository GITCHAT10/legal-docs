class BubbleInterface:
    def __init__(self, guard, events):
        self.guard = guard
        self.events = events

    def trigger_notification(self, actor_ctx: dict, user_id: str, message: str):
        return self.guard.execute_sovereign_action(
            "bubble.notify",
            actor_ctx,
            self._internal_notify,
            user_id, message
        )

    def _internal_notify(self, user_id, message):
        self.events.publish("bubble.notification_sent", {"user": user_id, "msg": message})
        return True
